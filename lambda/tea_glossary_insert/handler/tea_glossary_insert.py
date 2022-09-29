import json
import os
from functools import reduce
import boto3
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SPREADSHEET_ID = os.environ['spreadsheet_id']
API_KEY = os.environ['google_spreadsheet_api_key']

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SAMPLE_RANGE = 'A:B'
client = boto3.client('dynamodb')

def get_spreadsheet():
    try:
        service = build('sheets', 'v4', developerKey=API_KEY)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SAMPLE_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')

        return format_spreadsheet(values)
    except HttpError as err:
        print(err)

def split_entry(entry):
    keys = entry[0].split(", ")
    definition = entry[1]

    return list(map(lambda k: {'word': k, 'definition': definition}, keys))

def format_spreadsheet(values):
    glossary = []

    for row in values:
        if len(row) > 1:
            glossary.append(split_entry(row))

    return glossary

def insert_spreadsheet(spreadsheet):
    print('bulk insert in dynamodb')

def lambda_handler(event, context):
    spreadsheet = get_spreadsheet()
    insert_spreadsheet(spreadsheet)

    return {
        'statusCode': 200,
        'body': json.dumps(f'{API_KEY}:{SPREADSHEET_ID}')
    }

if __name__ == "__main__":
    print(lambda_handler(None, None))