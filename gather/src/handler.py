try:
    import unzip_requirements
except ImportError:
    pass

import json
import logging
from random import sample
import boto3

# serverless requires first import style, pytest requires second
try:
    from src.lambda_gather.utils import (
        get_lifeprint_dictionary_links,
        get_new_youtube_links_from_dictionary_content_page,
        lifeprint_dictionary_to_dynamodb,
        load_creds_env_gather,
        verify,
        dynamodb_scan,
        update_dynamodb_item,
    )

    EXTERNAL_RESOURCES_FILEPATH = "resources/external-resources.json"
except:
    from gather.src.lambda_gather.utils import (
        get_lifeprint_dictionary_links,
        get_new_youtube_links_from_dictionary_content_page,
        lifeprint_dictionary_to_dynamodb,
        load_creds_env_gather,
        verify,
        dynamodb_scan,
        update_dynamodb_item,
    )

    EXTERNAL_RESOURCES_FILEPATH = "gather/resources/external-resources.json"  # assuming tests run from the root of the project


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

    # Lifeprint
    letters = sample("abcdefghijklmnopqrstuvwxyz", 3)
    all_dictionary_pages = get_lifeprint_dictionary_links(
        sleep_time=0.01, letters=letters
    )
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

    external_resources = json.load(open(EXTERNAL_RESOURCES_FILEPATH))
    for entry in external_resources:
        if entry["url"] not in existing_urls:
            update_dynamodb_item(
                url=entry["url"],
                description=entry["description"],
                contentSource=entry.get("contentSource", ""),
                contentCreator=entry.get("contentCreator", ""),
                contentType=entry.get("contentType", ""),
                dynamodb_client=dynamodb_client,
                table_name=dynamodb_table_name,
            )

    return {
        "statusCode": 200,
        "body": json.dumps("ASL content dictionary successfully updated"),
    }
