import json
import boto3
import os
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

ssm = boto3.client('ssm')

print('hello')
PUBLIC_KEY = ssm.get_parameter(Name='/reyashibot/discord/DiscordPublicKey')
TABLE_NAME = os.environ['TABLE_NAME']
PING_PONG = {"type": 1}

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def search_definition(word):
    print(f'value searched: {word}')
    response = table.get_item(Key={'word': word.lower()})

    if not response.get('Item', None):
        return '🤔 No definition found'

    definition = response['Item']['definition']
    return f'**{word}**: {definition}'

def ping_pong(body):
    return body['type'] == 1

def verify_signature(body, timestamp, signature):   
    message = timestamp.encode() + body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(signature))
    
def get_word(json_body):
    return json_body['data']['options'][0]['value']

def lambda_handler(event, context):
    try:
        verify_signature(
            event['body'], 
            event['headers'].get('x-signature-timestamp'), 
            event['headers'].get('x-signature-ed25519')
        )
        print('signature valid')
    except BadSignatureError as e:
        print('problem with salt')
        return {
            'statusCode': 401,
            'body': json.dumps('signature invalid'),
        }
    
    json_body = json.loads(event['body'])
    
    if ping_pong(json_body):
        print('pong')
        return {
            'statusCode': 200,
            'body': json.dumps(PING_PONG),
        }

    word = get_word(json_body)
    definition = search_definition(word)
    
    return {
            'statusCode': 200,
            'body': json.dumps({
            "type": 4,
            "data": {
                "content": definition,
            }
        }),
        }
