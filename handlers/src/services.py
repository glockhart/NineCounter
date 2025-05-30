import boto3
import logging
import os
from boto3.dynamodb.conditions import Key

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB table name (can be set as an environment variable)
TABLE_NAME = os.environ.get('DDB_TABLE', 'AwsServiceSLAs')
logger.info("Reading from %s", TABLE_NAME)

_LAMBDA_DYNAMODB_RESOURCE = { "resource" : boto3.resource('dynamodb', region_name="eu-west-1"), 
                              "table_name" : TABLE_NAME }

class LambdaDynamoDBClass:
    """
    AWS DynamoDB Resource Class
    """
    def __init__(self, lambda_dynamodb_resource):
        """
        Initialize a DynamoDB Resource
        """
        self.resource = lambda_dynamodb_resource["resource"]
        self.table_name = lambda_dynamodb_resource["table_name"]
        self.table = self.resource.Table(self.table_name)


def lambda_handler(event, context):
    """
    AWS Lambda handler to return all AWS services and their SLA ranges from DynamoDB.
    """

    logger.info("Received event: %s", event)

    global _LAMBDA_DYNAMODB_RESOURCE

    dynamodb_resource_class = LambdaDynamoDBClass(_LAMBDA_DYNAMODB_RESOURCE)

    try:
        # Scan the table to get all items
        response = dynamodb_resource_class.table.scan()
        items = response.get('Items', [])
        logger.info("Fetched %d services from DynamoDB", len(items))

        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = dynamodb_resource_class.table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
            logger.info("Fetched additional %d services (pagination)", len(response.get('Items', [])))

        return {
            "statusCode": 200,
            "body": items
        }
    except Exception as e:
        logger.error("Error fetching services from DynamoDB: %s", e, exc_info=True)
        return {
            "statusCode": 500,
            "body": f"Error fetching services: {str(e)}"
        }
