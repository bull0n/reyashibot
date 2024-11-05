import json
import os
import boto3
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ssm = boto3.client('ssm')
SPREADSHEET_ID = ssm.get_parameter(Name='/reyashibot/spreadhseet/SpreadhseetId')['Parameter']['Value']
API_KEY = ssm.get_parameter(Name='reyashibot/spreadhseet/GoogleSpreadhseetApiKey')['Parameter']['Value']
TABLE_NAME = os.environ['TABLE_NAME']

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SAMPLE_RANGE = 'A:B'

def get_spreadsheet():
    try:
        service = build('sheets', 'v4', developerKey=API_KEY)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SAMPLE_RANGE).execute()
        values = result.get('values', [])

        if not values:
            raise Exception('No data found')

        return format_spreadsheet(values)
    except HttpError as err:
        print(err)

def split_entry(entry):
    keys = entry[0].split(", ")
    definition = entry[1]

    return list(map(lambda k: {'word': k.lower(), 'word_capitalized': k, 'definition': definition}, keys))

def format_spreadsheet(values):
    glossary = []

    for row in values:
        if len(row) > 1:
            glossary += split_entry(row)

    return glossary

def insert_spreadsheet(spreadsheet):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    spreadsheet_filtered = filter(lambda e: e['word'], spreadsheet)
    
    with table.batch_writer(overwrite_by_pkeys=['word']) as batch:
        for item in spreadsheet_filtered:
            batch.put_item(item)

def lambda_handler(event, context):
    spreadsheet = get_spreadsheet()
    insert_spreadsheet(spreadsheet)

    return {
        'statusCode': 200,
        'body': json.dumps(f'{API_KEY}:{SPREADSHEET_ID}')
    }