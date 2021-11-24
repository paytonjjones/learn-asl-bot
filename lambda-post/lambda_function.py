import json
import pickle
import boto3
from botocore import UNSIGNED
from botocore.client import Config

from utils import post_random_content, load_creds_aws


def lambda_handler(event, context):
    # Load from S3 bucket
    s3 = boto3.resource("s3", config=Config(signature_version=UNSIGNED))
    entire_dict = pickle.loads(
        s3.Bucket("lifeprintdict").Object("cached_dict").get()["Body"].read()
    )
    try:
        creds = load_creds_aws()
    except:
        creds = pickle.load(open("../creds", "rb"))

    # Post
    try:
        post_random_content(entire_dict, creds, content_type="youtube")
        return {
            "statusCode": 200,
            "body": json.dumps("Content posted with no exceptions"),
        }
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps("Error:" + str(e))}

