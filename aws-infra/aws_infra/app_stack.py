from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecsPatterns,
    aws_certificatemanager as acm,
    aws_codecommit as ccm,
    pipelines as cpl,
)
from constructs import Construct


class QuestAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        QuestMonorepo = ccm.Repository(
            self, "QuestMonorepo", repository_name="quest-monorepo"
        )

        AppMonoPipeline = cpl.CodePipeline(
            self,
            "QuestAppPipeline",
            pipeline_name="app-quest-pipeline",
            docker_enabled_for_self_mutation=True,
            docker_enabled_for_synth=True,
            synth=cpl.ShellStep(
                "Synth",
                input=cpl.CodePipelineSource.connection(
                    "JamesClick/quest", "master", connection_arn="arn:aws:codestar-connections:us-west-1:056389583808:connection/f67183aa-909c-44bd-b331-6150e2489b51"
                )
                commands=[
                    "python -m pip install -r requirements.txt",
                    "npx aws-cdk synth",
                ],
            ),
        )

        envVars = {"SECRET_WORD": "TwelveFactors"}
        domainName = "app.quest.jamesclick.net"

        # Requires manual action on console during CDK Deploy unless domain has been used on that account before
        # AND the CNAME verification record still exists.
        QuestAppCert = acm.Certificate(
            self,
            "QuestAppCert",
            domain_name=domainName,
            validation=acm.CertificateValidation.from_dns(),
        )

        QuestAppWebCluster = ecsPatterns.ApplicationLoadBalancedFargateService(
            self,
            "QuestWebServer",
            task_image_options=ecsPatterns.ApplicationLoadBalancedTaskImageOptions(
                # See https://github.com/aws/aws-cdk/issues/3899#issuecomment-580394612
                image=ecs.ContainerImage.from_asset("."),
                container_port=3000,
                environment=envVars,
            ),
            desired_count=1,
            certificate=QuestAppCert,
            public_load_balancer=True,
            redirect_http=True,
        )

        # This and utilization values should be adjusted over time to best suit the runtime.
        # Currently set to reasonable values to allow some flexibility.
        scalable_target = QuestAppWebCluster.service.auto_scale_task_count(
            min_capacity=1, max_capacity=10
        )

        scalable_target.scale_on_cpu_utilization(
            "CpuScaling", target_utilization_percent=50
        )

        scalable_target.scale_on_memory_utilization(
            "MemoryScaling", target_utilization_percent=50
        )
