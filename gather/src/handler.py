try:
    import unzip_requirements
except ImportError:
    pass

import json
import logging
import boto3

from src.lambda_gather.utils import (
    get_lifeprint_dictionary_links,
    get_youtube_links_from_dictionary_content_page,
    lifeprint_dictionary_to_dynamodb,
    load_creds_env_gather,
    verify,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_gather(event, context):
    creds = load_creds_env_gather()
    dynamodb_client = boto3.client(
        "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
    )
    try:
        all_dictionary_pages = get_lifeprint_dictionary_links(0.01)
        for dictionary_word, url in all_dictionary_pages.items():
            new_entries = get_youtube_links_from_dictionary_content_page(
                url, dictionary_word
            )
            lifeprint_dictionary_to_dynamodb(
                new_entries, "asl_resource_dict", dynamodb_client
            )
    except Exception as e:
        return {"statusCode": 400, "body": json.dumps("Error:" + str(e))}
    return {
        "statusCode": 200,
        "body": json.dumps("ASL content dictionary successfully updated"),
    }
