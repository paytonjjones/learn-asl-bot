import json
import logging
import os
import time
import requests
import re
import random
import praw
import dotenv
from boto3.dynamodb.conditions import Key
from bs4 import BeautifulSoup

dotenv.load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TIMEOUT_SECONDS = 5


def post_from_dynamodb(reddit_creds, dynamodb_resource, dynamodb_client, table_name):
    reddit_post_success = True
    dynamo_update_success = True
    all_entries = dynamodb_scan(dynamodb_resource, table_name)
    times_posted = [
        dict.get("timesPosted")
        for dict in all_entries
        if dict.get("timesPosted") is not None
    ]
    least_posted_entries = [
        entry for entry in all_entries if entry.get("timesPosted") == min(times_posted)
    ]
    chosen_content = random.choice(least_posted_entries)
    is_valid_link = validate_link(chosen_content["url"], chosen_content["description"])
    if is_valid_link:
        try:
            post_youtube(chosen_content, reddit_creds)
        except Exception as e:
            logger.info(e)
            logger.info("Error posting to Reddit")
            logger.info(chosen_content)
            reddit_post_success = False
    else:
        logger.info("Invalid link")
        logger.info(chosen_content["url"])
        reddit_post_success = False
    updated_times_posted = str(chosen_content.get("timesPosted") + 1)
    try:
        dynamodb_client.update_item(
            TableName=table_name,
            Key={"url": {"S": chosen_content["url"]}},
            UpdateExpression="set timesPosted=:t, timestampLastPosted=:s",
            ExpressionAttributeValues={
                ":t": {"N": updated_times_posted},
                ":s": {"N": str(int(time.time()))},
            },
            ReturnValues="UPDATED_NEW",
        )
    except Exception as e:
        logger.info(e)
        logger.info(chosen_content["url"])
        dynamo_update_success = False
    statusCode = 200 if reddit_post_success and dynamo_update_success else 400
    message = ""
    message += (
        "Error posting to Reddit; "
        if not reddit_post_success
        else "Content successfully posted to Reddit; "
    )
    message += (
        "Error updating DynamoDB"
        if not dynamo_update_success
        else "Content successfully updated on DynamoDB"
    )
    return {"statusCode": statusCode, "body": json.dumps(message)}


def smart_truncate(content, length=300, suffix="..."):
    # from https://stackoverflow.com/questions/250357/truncate-a-string-without-ending-in-the-middle-of-a-word
    if len(content) <= length:
        return content
    else:
        return " ".join(content[: length + 1].split(" ")[0:-1]) + suffix


def post_youtube(content_dict, reddit_creds):
    title = clean_description(content_dict["description"])
    url = content_dict["url"]
    session = requests.Session()
    session.verify = False  # Disable SSL warnings
    reddit = praw.Reddit(
        user_agent="test",
        client_id=reddit_creds["CLIENT_ID"],
        client_secret=reddit_creds["CLIENT_SECRET"],
        username=reddit_creds["USERNAME"],
        password=reddit_creds["PASSWORD"],
        requestor_kwargs={"session": session},
    )
    reddit.validate_on_submit = True
    reddit.subreddit("learnASL").submit(title=title, url=url)
    logger.info("YouTube embedded video posted to Reddit")


def load_creds_env():
    creds = {}
    creds["CLIENT_ID"] = os.environ["CLIENT_ID"]
    creds["CLIENT_SECRET"] = os.environ["CLIENT_SECRET"]
    creds["USERNAME"] = os.environ["USERNAME"]
    creds["PASSWORD"] = os.environ["PASSWORD"]
    creds["AWS_REGION"] = os.environ["AWS_REGION"]
    creds["DYNAMODB_TABLE_NAME"] = os.environ["DYNAMODB_TABLE_NAME"]
    return creds


# TODO:
##  COMMON FUNCTIONS


def validate_link(url, description):
    if "youtube" not in url.lower():
        return False
    if "youtube.com/billvicars" in url.lower():
        return False
    if "video coming soon" in description.lower():
        return False
    if not " " in description.lower():
        return False
    if "playlist" in description.lower():
        return False
    if "quiz" in description.lower():
        return False
    return True


def clean_description(title):
    title = re.sub("(\n|\t|\r)+", "", title)  # remove newlines
    title = re.sub("\s\s+", " ", title)  # remove double spaces
    title = re.sub("^\d+\.", "", title)  # remove preceding numbers like 09.
    title = re.sub("\:$", "", title)  # remove : at the end
    title = title.strip()
    title = smart_truncate(title)
    return title


def smart_truncate(content, length=300, suffix="..."):
    # from https://stackoverflow.com/questions/250357/truncate-a-string-without-ending-in-the-middle-of-a-word
    if len(content) <= length:
        return content
    else:
        return " ".join(content[: length + 1].split(" ")[0:-1]) + suffix


def dynamodb_scan(dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    scan = table.scan()
    return scan["Items"]


def verify():
    verify_str = os.environ["VERIFY"]
    if verify_str == "True":
        return True
    else:
        return False
