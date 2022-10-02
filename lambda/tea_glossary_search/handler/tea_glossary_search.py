import json
import boto3
import os
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


PUBLIC_KEY = os.environ['discord_public_key']
TABLE_NAME = os.environ['TABLE_NAME']
PING_PONG = {"type": 1}

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def search_definition(word):
    response = table.get_item(Key={'word': {'S': word}})

    if not response:
        return '🤔 No definition found'

    return response['definition']

def ping_pong(body):
    return body.get("type") == 1

def verify_signature(body, timestamp, signature):   
    message = timestamp.encode() + body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(signature))

def lambda_handler(event, context):
    print(event) #debug 

    try:
        verify_signature(
            event['body'], 
            event['params']['header'].get('x-signature-timestamp'), 
            event['params']['header'].get('x-signature-ed25519')
        )
    except BadSignatureError as e:
        return {
            'statusCode': 401,
            'body': json.dumps("signature invalid"),
        }

    if ping_pong(event['body']):
        return PING_PONG

    word = 'twl'
    definition = search_definition(word)
    return {
        'statusCode': 200,
        'body': json.dumps(definition)
    }
