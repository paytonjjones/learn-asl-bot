import logging
import os
import time
import dotenv
import requests
import re
from boto3.dynamodb.conditions import Key

from bs4 import BeautifulSoup


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dotenv.load_dotenv()


def verify():
    verify_str = os.environ["VERIFY"]
    if verify_str == "True":
        return True
    else:
        return False


def get_lifeprint_dictionary_links(
    sleep_time=0.01, letters="abcdefghijklmnopqrstuvwxyz"
):
    stem = "https://lifeprint.com/asl101/index/"
    full_dict = {}
    for letter in letters:
        letter_dict = parse_lifeprint_dictionary_main_page(stem + letter + ".htm")
        full_dict.update(letter_dict)
        time.sleep(sleep_time)
    return full_dict


def parse_lifeprint_dictionary_main_page(url):
    """
    The dictionary main page contains links to subpages with words.
    Takes a url (ex. https://lifeprint.com/asl101/index/a.htm)
    Returns a dictionary with the dictionary entry as the key,
    and the link to the dictionary content page as the value
    """
    page = requests.get(url, verify=verify())
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


def get_youtube_links_from_dictionary_content_page(
    url, dictionary_word, sleep_time=0.01
):
    """
    The content page contains images and videos describing the word
    Takes a url (ex. https://lifeprint.com/asl101//pages-signs/a/active.htm)
    Returns a dictionary with the url as key
    """
    time.sleep(sleep_time)
    page = requests.get(url, verify=verify())
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    video_dict = {}
    for video in videos:
        url = video["src"]
        value_dict = {}
        value_dict["description"] = get_dictionary_description(video, dictionary_word)
        value_dict["contentSource"] = "lifeprint-dictionary"
        value_dict["contentCreator"] = "Bill Vicars"
        value_dict["contentType"] = "youtube"
        video_dict[url] = value_dict
    return video_dict


def lifeprint_dictionary_to_dynamodb(
    video_dict, table_name="asl_resource_dict", dynamodb_client=None
):
    for url, item_info in video_dict.items():
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


def get_dictionary_description(bs4_element, dictionary_word):
    text_array = []
    temp = bs4_element
    while True:
        temp = temp.previous
        if temp.name == "hr" or temp.name == "font":
            break
        if isinstance(temp, type("bs4.element.NavigableString")):
            text_array.append(temp)
    # reverse text_array, then
    text_array.reverse()
    raw_description = "".join(text_array)
    full_description = dictionary_word + " | " + raw_description
    description = clean_description(full_description)
    return description


def clean_description(title):
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


def query_dynamodb_by_key(key, dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    response = table.query(KeyConditionExpression=Key("url").eq(key))
    return response["Items"]


def load_creds_env_gather():
    creds = {}
    creds["AWS_REGION"] = os.environ["AWS_REGION"]
    creds["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
    creds["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
    return creds

