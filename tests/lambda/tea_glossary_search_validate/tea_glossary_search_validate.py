import boto3
import os

client = boto3.client('lambda', endpoint_url='http://host.docker.internal:3001')
LAMBDA_NAME = os.environ['LAMBDA_NAME']

with open('event.json') as f: PAYLOAD = f.read()


def lambda_handler(event, context):
    response = client.invoke(FunctionName=LAMBDA_NAME, InvocationType='RequestResponse', Payload=PAYLOAD)

    return True