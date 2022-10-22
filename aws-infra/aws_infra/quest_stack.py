from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecsPatterns,
    pipelines as cpl,
    aws_secretsmanager as secretmanager,
    aws_ec2 as ec2,
    SecretValue,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
)
from constructs import Construct


class QuestAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Rolling both app and infra updates into one pipeline due to low change frequency.
        MonoPipeline = cpl.CodePipeline(
            self,
            "quest-app-pipeline",
            pipeline_name="quest-app-pipeline",
            docker_enabled_for_self_mutation=True,
            docker_enabled_for_synth=True,
            synth=cpl.ShellStep(
                "Synth",
                input=cpl.CodePipelineSource.connection(
                    "lastnameclick/quest",
                    "master",
                    connection_arn="arn:aws:codestar-connections:us-west-1:056389583808:connection/f67183aa-909c-44bd-b331-6150e2489b51",
                ),
                commands=[
                    "python -m pip install -r requirements.txt",
                    "npx aws-cdk synth",
                ],
            ),
        )

        # Using self-signed certificate for HTTPS, see README for information on prerequisites.
        certificate = acm.Certificate.from_certificate_arn(
            self,
            "quest-selfsigned-certificate",
            certificate_arn="arn:aws:acm:us-west-1:056389583808:certificate/8bf5cbd8-65bf-434b-9c35-6d958381ea78",
        )

        vpc = ec2.Vpc(self, "Vpc", max_azs=3)
        cluster = ecs.Cluster(self, "EcsCluster", vpc=vpc)

        SecretWord = secretmanager.Secret(
            self,
            "quest-secret-word",
            secret_object_value={
                # Typically ill-advised to declare a secret in this manner (visible from CFN stack), risk accepted for this example.
                "SECRET_WORD": SecretValue.unsafe_plain_text("TwelveFactors")
            },
        )

        # FargateService pattern will not selfgen an HTTPS cert due to ELB involvement.
        QuestAppWebCluster = ecsPatterns.ApplicationLoadBalancedFargateService(
            self,
            "quest-web-service",
            cluster=cluster,
            task_image_options=ecsPatterns.ApplicationLoadBalancedTaskImageOptions(
                # See https://github.com/aws/aws-cdk/issues/3899#issuecomment-580394612
                image=ecs.ContainerImage.from_asset("."),
                container_port=3000,
                secrets={
                    "SECRET_WORD": ecs.Secret.from_secrets_manager(secret=SecretWord)
                },
            ),
            desired_count=1,
            public_load_balancer=True,
            redirect_http=True,
            certificate=certificate,
            protocol=elbv2.ApplicationProtocol.HTTPS,
        )

        SecretWord.grant_read(QuestAppWebCluster.task_definition.execution_role)

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
