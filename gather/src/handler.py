try:
    import unzip_requirements
except ImportError:
    pass

import json
import logging
import boto3

from gather.src.lambda_gather.utils import (
    get_lifeprint_dictionary_links,
    get_new_youtube_links_from_dictionary_content_page,
    lifeprint_dictionary_to_dynamodb,
    load_creds_env_gather,
    verify,
    dynamodb_scan,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_gather(event, context):
    dynamodb_table_name = "asl_resource_dict"
    creds = load_creds_env_gather()
    dynamodb_client = boto3.client(
        "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
    )
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
    )
    all_dictionary_pages = get_lifeprint_dictionary_links(0.01)
    saved_entries = dynamodb_scan(dynamodb_resource, dynamodb_table_name)
    existing_urls = [entry["url"] for entry in saved_entries]

    for dictionary_word, url in all_dictionary_pages.items():
        try:
            new_entries = get_new_youtube_links_from_dictionary_content_page(
                url, dictionary_word, existing_urls
            )
            if new_entries:
                lifeprint_dictionary_to_dynamodb(
                    new_entries, dynamodb_table_name, dynamodb_client
                )
        except Exception as e:
            logger.info(
                "Error in getting YouTube links for" + dictionary_word + ": " + str(e)
            )
    return {
        "statusCode": 200,
        "body": json.dumps("ASL content dictionary successfully updated"),
    }
