import os
import uuid
import time
import json
import base64
import random
import boto3
from botocore.exceptions import NoCredentialsError
import urllib.parse
import urllib.request

# Set up your OpenAI API credentials


def get_shopping_list_emoji(shopping_item):
    api_key = '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'
    # Define the prompt
    prompt = f"find an appropriate emoji for the following shopping list item: '{shopping_item}'."

    # Call the GPT-3.5 API to generate the response
    data = {
        'prompt': prompt,
        'max_tokens': 10,
        'n': 1,
        'stop': None,
        'temperature': 0.0
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = json.dumps(data).encode('utf-8')

    # Make the API call
    url = 'https://api.openai.com/v1/engines/text-davinci-003/completions'
    req = urllib.request.Request(url, data=data, headers=headers)
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode('utf-8'))
    print(result)
    emoji = result['choices'][0]['text'].strip()
    print(emoji)
    # Extract the generated emoji from the response

    return emoji + '  ' + shopping_item


def handler(event, context):
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    textract = boto3.client('textract')

    # Get bucket and table name from environment variables
    bucket_name = os.environ['RECEIPTS_BUCKET_NAME']
    table_name = os.environ['RECEIPTSTABLE_TABLE_NAME']
    table = dynamodb.Table(table_name)
    print(event)
    # parse event for file information
    file_content = base64.b64decode(json.loads(event['body'])['file'])
    file_name = str(uuid.uuid4()) + '.jpg'

    # Save file to S3
    try:
        s3_response = s3.put_object(
            Bucket=bucket_name, Key=file_name, Body=file_content)
    except NoCredentialsError:
        return {
            'statusCode': 401,
            'body': 'No AWS credentials found'
        }

     # Start the Textract Analysis job
    response = textract.start_expense_analysis(
        DocumentLocation={
            'S3Object':
            {
                'Bucket': bucket_name,
                'Name': file_name
            }
        })

    # Get the job id
    job_id = response['JobId']

    # Wait for Textract job to complete
    while True:
        response = textract.get_expense_analysis(JobId=job_id)
        print(response)
        status = response['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            break

        print("Waiting for Textract job to complete...")
        time.sleep(2)

    # If the job succeeded, store results in DynamoDB
    if status == 'SUCCEEDED':
        table = dynamodb.Table('sam-app-ReceiptsTable-EEZSGS6MY0P2')
        print(response)
        for expense in response['ExpenseDocuments']:
            vendor = ''
            date = ''
            for summary_field in expense['SummaryFields']:
                if summary_field['Type']['Text'] == 'NAME':
                    vendor = summary_field['ValueDetection']['Text']
                if summary_field['Type']['Text'] == 'INVOICE_RECEIPT_DATE':
                    date = summary_field['ValueDetection']['Text']
            for group in expense['LineItemGroups']:
                for item in group['LineItems']:
                    print(item)
                    record = {
                        'id': str(random.randint(0, 9999999)),
                        'date': date,
                        'vendor': vendor
                    }
                    for field in item['LineItemExpenseFields']:
                        if field['Type']['Text'] == 'ITEM':
                            record['name'] = get_shopping_list_emoji(
                                field['ValueDetection']['Text'])
                        if field['Type']['Text'] == 'PRICE':
                            record['price'] = field['ValueDetection']['Text']
                    print(record)

                    res = table.put_item(Item=record)
                    print(res)

    return {
        'statusCode': 200,
        'body': f"Expense Analysis job {status}"
    }
