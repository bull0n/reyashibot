import boto3
import os

ENDPOINT = 'http://localhost:3001/' if bool(os.environ['AWS_SAM_LOCAL']) else None
lambda_client = boto3.client('lambda', endpoint_url=ENDPOINT)
codedeploy_client = boto3.client('codedeploy')
LAMBDA_NAME = os.environ

with open('event.json') as f: PAYLOAD = f.read()

def lambda_handler(event, context):
    try:
        lambda_client.invoke(FunctionName=LAMBDA_NAME, InvocationType='RequestResponse', Payload=PAYLOAD)
    except:
        codedeploy_client.put_lifecycle_event_hook_execution_status(
            deploymentId=event['DeploymentId'],
            lifecycleEventHookExecutionId=event['LifecycleEventHookExecutionId'],
            status='Failed'
        )

    return codedeploy_client.put_lifecycle_event_hook_execution_status(
        deploymentId=event['DeploymentId'],
        lifecycleEventHookExecutionId=event['LifecycleEventHookExecutionId'],
        status='Succeeded'
    )