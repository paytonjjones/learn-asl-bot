try:
    import unzip_requirements
except ImportError:
    pass

import logging
import json
import boto3

from src.lambda_post.utils import post_from_dynamodb, load_creds_env, verify

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_post(event, context):
    creds = load_creds_env()

    try:
        dynamodb_client = boto3.client(
            "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
        )
        dynamodb_resource = boto3.resource(
            "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
        )
        response = post_from_dynamodb(
            creds, dynamodb_resource, dynamodb_client, creds["DYNAMODB_TABLE_NAME"]
        )
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps("Error:" + str(e))}
    return response

