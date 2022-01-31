try:
    import unzip_requirements
except ImportError:
    pass

import logging
import json
import pickle
import boto3
from botocore import UNSIGNED
from botocore.client import Config

from src.lambda_post.utils import post_random_content, load_creds_env

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_post(event, context):
    # Load from S3 bucket
    s3 = boto3.resource("s3", config=Config(signature_version=UNSIGNED))
    entire_dict = pickle.loads(
        s3.Bucket("lifeprintdict").Object("cached_dict").get()["Body"].read()
    )
    creds = load_creds_env()

    # Post
    try:
        post_random_content(entire_dict, creds, content_type="youtube")
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps("Error:" + str(e))}
    return {
        "statusCode": 200,
        "body": json.dumps("Content successfully posted to Reddit"),
    }

