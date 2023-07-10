import os
import json
import boto3
from boto3.dynamodb.conditions import Key

def handler(event, context):
    # Fetch table name from environment variable
    table_name = os.getenv('RECEIPTSTABLE_TABLE_NAME')
    
    # Initialize a DynamoDB client 
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Fetch all items from DynamoDB table
    response = table.scan()
    items = response['Items']

    # Convert the items to JSON format
    items_json = json.dumps(items, default=str)

    return {
        'statusCode': 200,
        'body': items_json,
        'headers': {
            'Content-Type': 'application/json'
        },
    }
