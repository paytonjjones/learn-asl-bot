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

# import aws_cdk.aws_ssm as ssm


def post_from_dynamodb(reddit_creds, dynamodb_resource, dynamodb_client, table_name):
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
    post_youtube(chosen_content, reddit_creds)
    try:
        dynamodb_client.update_item(
            TableName=table_name,
            Key={"url": {"S": chosen_content["url"]}},
            UpdateExpression="set timesPosted=:t, timestampLastPosted=:s",
            ExpressionAttributeValues={
                ":t": {"N": chosen_content.get("timesPosted") + 1},
                ":s": {"N": time.time()},
            },
            ReturnValues="UPDATED_NEW",
        )
    except Exception as e:
        logger.info(e)
        logger.info(chosen_content["url"])


def parse_dictionary_content_page(url, name):
    """
    The content page contains images and videos describing the word
    Takes a url (ex. https://lifeprint.com/asl101//pages-signs/a/active.htm)
    Returns a pandas dataframe as follows:
    # pandas df:
    # name
    # type ("image", "gif", or "video")
    # text
    # location (the web address where the content can be found)
    """
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    video_dict = {}
    for video in videos:
        row = {}
        row["name"] = name
        row["type"] = "youtube"
        row["text"] = get_description(video)
        row["location"] = video["src"]
        video_dict[name] = row
    return video_dict


def get_description(element):
    text_array = []
    temp = element
    while True:
        temp = temp.previous
        if temp.name == "hr" or temp.name == "font":
            break
        if isinstance(temp, type("bs4.element.NavigableString")):
            text_array.append(temp)
    # reverse text_array, then
    text_array.reverse()
    description = "".join(text_array)
    # Clean for Reddit Title
    description = re.sub("(\n|\t)+", "", description)
    description = smart_truncate(description)
    return description


def smart_truncate(content, length=300, suffix="..."):
    # from https://stackoverflow.com/questions/250357/truncate-a-string-without-ending-in-the-middle-of-a-word
    if len(content) <= length:
        return content
    else:
        return " ".join(content[: length + 1].split(" ")[0:-1]) + suffix


def post_youtube(content_dict, reddit_creds):
    title = content_dict["description"]
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
