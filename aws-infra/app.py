#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_infra.quest_stack import QuestAppStack


app = cdk.App()
QuestAppStack(
    app,
    "QuestAppStack",
    env=cdk.Environment(account="056389583808", region="us-west-1"),
)

app.synth()
