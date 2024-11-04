#!/usr/bin/env python3
import os

import aws_cdk as cdk

from reyashibot.reyashibot_stack import ReyashibotStack


app = cdk.App()
ReyashibotStack(app, 'ReyashibotStack',env=cdk.Environment(account=os.environ['ACCOUNT'], region=os.environ['REGION']))

app.synth()
