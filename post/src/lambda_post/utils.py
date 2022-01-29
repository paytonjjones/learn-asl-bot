import logging
import os
import requests
import re
import random
import praw
import pickle

from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# import aws_cdk.aws_ssm as ssm


def post_random_content(main_page, reddit_creds, content_type="random"):
    if content_type == "random":
        content_type = random.choice(["image", "youtube", "mp4"])
    content_dict = {}
    i = 0
    while True:
        name = random.choice([*main_page.keys()])
        url = main_page[name]
        content_dict = parse_dictionary_content_page(url, name)
        i += 1
        if i > 100 or len(content_dict) > 0:
            break
    chosen_content = content_dict[random.choice([*content_dict.keys()])]
    if content_type == "image":
        pass
    elif content_type == "youtube":
        post_youtube(chosen_content, reddit_creds)
    elif content_type == "mp4":
        pass
    return chosen_content


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
    title = content_dict["name"] + " | " + content_dict["text"]
    url = content_dict["location"]
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
    return creds
