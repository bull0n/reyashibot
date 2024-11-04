import boto3
import os

client = boto3.client('lambda')

PAYLOAD = {
    "hello": None
}

def lambda_handler(event, context):

    client.invoke(LAMBDA_NAME, InvocationType='Event', payload=None)

    return True