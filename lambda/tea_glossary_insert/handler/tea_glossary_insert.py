import json
import os
import boto3
from googleapiclient.discovery import build

SPREADSHEET_ID = os.environ['spreadsheet_id']
API_KEY = os.environ['google_spreadsheet_api_key']

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SAMPLE_RANGE = 'A:B'
client = boto3.client('dynamodb')

def get_spreadsheet():
    try:
        service = build('sheets', 'v4', developerKey=API_KEY)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=SAMPLE_RANGE).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')

        print(values)
    except HttpError as err:
        print(err)

def insert_spreadsheet(spreadsheet):
    print('hello')

def lambda_handler(event, context):
    spreadsheet = get_spreadsheet()
    insert_spreadsheet(spreadsheet)

    return {
        'statusCode': 200,
        'body': json.dumps(f'{API_KEY}:{SPREADSHEET_ID}')
    }
