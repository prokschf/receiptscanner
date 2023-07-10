import csv
import boto3
from botocore.exceptions import NoCredentialsError

def delete_all_items(table_name, region_name='us-west-2'):
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(table_name)
    scan = table.scan()

    with table.batch_writer() as batch:
        for each in scan['Items']:
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    print("All items deleted from table: ", table_name)


def upload_to_dynamodb(file_name, table_name, region):
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    k = 0
    with open(file_name, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # skip header
        for row in reader:
            k = k + 1
            item = {
                'id': str(k),
                'name': row[1],
                'price': row[2],
                'vendor': row[3],
                'date': row[4]
            }
            table.put_item(Item=item)

if __name__ == "__main__":
    try:
        delete_all_items('sam-app-ReceiptsTable-EEZSGS6MY0P2', 'us-east-2')
        upload_to_dynamodb('list.csv', 'sam-app-ReceiptsTable-EEZSGS6MY0P2', 'us-east-2')
        print("Upload successful.")
    except NoCredentialsError:
        print("No AWS credentials found.")

