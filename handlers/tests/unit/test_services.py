import boto3
import moto
from aws_lambda_powertools.utilities.validation import validate
import json
import sys
import os
import logging
import pytest
from unittest.mock import MagicMock, patch
from unittest import TestCase
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '../..'))
sys.path.insert(1, os.path.join(sys.path[0], '../../..'))

from initialisation import dynamo_db_setup
from handlers.src import services
from handlers.src.services import LambdaDynamoDBClass   # pylint: disable=wrong-import-position
from handlers.src.services import lambda_handler  # pylint: disable=wrong-import-position


logger = logging.getLogger()
logger.setLevel(logging.INFO)

@moto.mock_aws
class TestServices(TestCase):
    
    def setUp(self) -> None:
        logger.info("Executing setup method")
        #Create a mock dynamodb
        #dynamodb = boto3.resource('dynamodb')
        #mocked_dynamodb_resource = dynamodb
        mocked_dynamodb_resource = { "resource" : boto3.resource('dynamodb'),
                                     "table_name" : "AwsServiceSLAs"  }

        self.mocked_dynamodb_class = LambdaDynamoDBClass(mocked_dynamodb_resource)

        self.expectedCount = dynamo_db_setup.initialise(self.mocked_dynamodb_class.resource,"../initialisation/aws_service_slas.json")
        

    def load_sample_event_from_file(self, test_event_file_name: str) ->  dict:
        """
        Loads and validate test events from the file system
        """
        event_file_name = f"tests/events/{test_event_file_name}.json"
        with open(event_file_name, "r", encoding='UTF-8') as file_handle:
            event = json.load(file_handle)
            #validate(event=event, schema=INPUT_SCHEMA)
            return event


    @patch("handlers.src.services.LambdaDynamoDBClass")
    def test_handler_reads_all_services(self,
                                        patch_lambda_dynamodb_class : MagicMock):
        try:
            patch_lambda_dynamodb_class.return_value = self.mocked_dynamodb_class

            test_event = self.load_sample_event_from_file("sampleEvent1")
            result = services.lambda_handler(event=test_event, context=None)
            logger.info("got a result %s", result)
            body = result.get("body", [])
            assert self.expectedCount == len(body)
        except Exception as e:
            raise
