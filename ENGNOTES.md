# Development Logbook

## 2022 OCT 22 @ssrc - TODO
---
 - (1) Implement WebApp Pipeline
 - (3) CDK unittests
 - (3) Continuous Testing
    - Depends on CDK/WebApp unittests
 - (4) Break out Infra from WebApp components into separate stacks
 - (5) WebApp unittests

## 2022 OCT 21 @ssrc - Building Fargate Container on Apple Silicon (AS)
---
Issue: Containers built with `linux/arm64` systems are not supported on AWS Fargate, which is used by Quest for Web.

Workaround: First setup Docker Buildx to your liking, being sure to include a `linux/amd64` option. Set the Envrionment Variable to use that container type.
```bash
export DOCKER_DEFAULT_PLATFORM='linux/amd64'
```

## 2022 OCT 21 @ssrc - ENAMETOOLONG when attempting to synthesize
---
Issue: ENAMETOOLONG raised when attempting to run `cdk synth`

Cause: Docker is attempting to iterate through cdk.out, which includes a filename (foldername?) that would be traditionally too long.

Workaround: Ignore `cdk.out` in the `.Dockerignore` (already done in this repo)

Remarks: CDK CLI (and/or docker runtime) base .dockerignore paths off of the contextual path, meaning you need to ignore the filepath relative to where you're going to be running the command.