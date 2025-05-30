import boto3
import time
import json
import logging
import os
from botocore.exceptions import ClientError
from decimal import Decimal

REGION = 'eu-west-1'
TABLE_NAME = 'AwsServiceSLAs'
JSON_FILE = './initialisation/aws_service_slas.json'

# Configure logger
logger = logging.getLogger("AwsServiceSLAsLoader")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def create_table(dynamodb):
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'ServiceName', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'ServiceName', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        logger.info("Creating table...")
        table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
        logger.info("Table created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info("Table already exists.")
        else:
            logger.error(f"Error creating table: {e}")
            raise

def load_services_from_json(filename):
    try:
        with open(filename, 'r') as f:
            services = json.load(f, parse_float=Decimal)
        logger.info(f"Loaded {len(services)} services from {filename}")
        return services
    except Exception as e:
        logger.error(f"Failed to load services from {filename}: {e}")
        raise

def populate_table(dynamodb, services) -> int:
    table = dynamodb.Table(TABLE_NAME)
    count = 0
    for service in services:
        try:
            table.put_item(Item=service)
            logger.info(f"Added {service['ServiceName']}")
            count+=1
        except Exception as e:
            logger.error(f"Failed to add {service['ServiceName']}: {e}")

    return count

def initialise(dynamodb, json_filename) -> int:
    create_table(dynamodb)
    time.sleep(5)  # Wait for table to be ready
    services = load_services_from_json(json_filename)
    return populate_table(dynamodb, services)

def main():
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    initialise(dynamodb, JSON_FILE)

if __name__ == '__main__':
    main()
