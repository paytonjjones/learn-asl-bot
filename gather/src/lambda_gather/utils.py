from datetime import datetime
import logging
import time
import requests
import re
import boto3
from boto3.dynamodb.conditions import Key

from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

letters = "abcdefghijklmnopqrstuvwxyz"


def get_lifeprint_dictionary_links(sleepTime=0.05, letters=letters):
    stem = "https://lifeprint.com/asl101/index/"
    full_dict = {}
    for letter in letters:
        letter_dict = parse_lifeprint_dictionary_main_page(stem + letter + ".htm")
        full_dict.update(letter_dict)
        time.sleep(sleepTime)
    return full_dict


def parse_lifeprint_dictionary_main_page(url):
    """
    The dictionary main page contains links to subpages with words.
    Takes a url (ex. https://lifeprint.com/asl101/index/a.htm)
    Returns a dictionary with the dictionary entry as the key,
    and the link to the dictionary content page as the value
    """
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    links_html = soup.find_all("a", href=True)
    links_html = [link for link in links_html if len(link.parent) > 1]
    master_dict = {}
    for blob in links_html:
        dictionary_word = clean_dictionary_word(blob.text)
        link = blob.get("href")
        link = re.sub("\.\.", "https://lifeprint.com/asl101/", link)
        master_dict[dictionary_word] = link
    return master_dict


def get_youtube_links_from_dictionary_content_page(url, dictionary_word):
    """
    The content page contains images and videos describing the word
    Takes a url (ex. https://lifeprint.com/asl101//pages-signs/a/active.htm)
    Returns a dictionary with the url as key
    """
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    video_dict = {}
    for video in videos:
        url = video["src"]
        value_dict = {}
        full_description = get_description(video)
        description = dictionary_word + " | " + full_description
        value_dict["description"] = clean_reddit_title(description)
        value_dict["contentSource"] = "lifeprint-dictionary"
        value_dict["contentCreator"] = "Bill Vicars"
        value_dict["contentType"] = "youtube"
        video_dict[url] = value_dict
    return video_dict


def lifeprint_dictionary_to_dynamodb(video_dict, table_name, dynamodb_client=None):
    for url, item_info in video_dict.items():
        logger.info(item_info)
        description = item_info.get("description")
        contentSource = item_info.get("contentSource")
        contentCreator = item_info.get("contentCreator")
        contentType = item_info.get("contentType")
        try:
            dynamodb_client.update_item(
                TableName=table_name,
                Key={"url": {"S": url}},
                UpdateExpression="set description=:d, contentSource=:s, contentCreator=:c, contentType=:t",
                ExpressionAttributeValues={
                    ":d": {"S": description},
                    ":s": {"S": contentSource},
                    ":c": {"S": contentCreator},
                    ":t": {"S": contentType},
                },
                ReturnValues="UPDATED_NEW",
            )
        except Exception as e:
            logger.info(e)
            logger.info(url)
            logger.info(item_info)


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
    return description


def query_dynamodb_by_key(key, dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    response = table.query(KeyConditionExpression=Key("url").eq(key))
    return response["Items"]


def clean_reddit_title(title):
    title = re.sub("(\n|\t)+", "", title)
    title = smart_truncate(title)
    return title


def smart_truncate(content, length=300, suffix="..."):
    # from https://stackoverflow.com/questions/250357/truncate-a-string-without-ending-in-the-middle-of-a-word
    if len(content) <= length:
        return content
    else:
        return " ".join(content[: length + 1].split(" ")[0:-1]) + suffix


def clean_dictionary_word(word):
    word = word.replace("\n", "")
    word = word.replace(" ", "")
    word = word.replace('"', "")
    return word
