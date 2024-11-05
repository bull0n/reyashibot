import boto3
import os

lambda_client = boto3.client('lambda')
LAMBDA_NAME = os.environ['LAMBDA_NAME']
codedeploy_client = boto3.client('codedeploy')

with open('event.json') as f: PAYLOAD = f.read()


def lambda_handler(event, context):
    print(event)
    try:
        response = lambda_client.invoke(FunctionName=LAMBDA_NAME, InvocationType='RequestResponse', Payload=PAYLOAD)
    except:
        return codedeploy_client.put_lifecycle_event_hook_execution_status(
        deploymentId=event['DeploymentId'],
        lifecycleEventHookExecutionId=event['LifecycleEventHookExecutionId'],
        status='Failed'
    )
    

    return codedeploy_client.put_lifecycle_event_hook_execution_status(
        deploymentId=event['DeploymentId'],
        lifecycleEventHookExecutionId=event['LifecycleEventHookExecutionId'],
        status='Succeeded'
    )