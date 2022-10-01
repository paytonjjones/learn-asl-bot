import logging
import os
import time
import dotenv
import requests
import re
import validators
from boto3.dynamodb.conditions import Key

from bs4 import BeautifulSoup


logger = logging.getLogger()
logger.setLevel(logging.INFO)

dotenv.load_dotenv()

TIMEOUT_SECONDS = 5


def verify():
    verify_str = os.environ["VERIFY"]
    if verify_str == "True":
        return True
    else:
        return False


def get_lifeprint_dictionary_links(
    sleep_time=0.01, letters="abcdefghijklmnopqrstuvwxyz"
):
    try:
        stem = "https://lifeprint.com/asl101/index/"
        full_dict = {}
        for letter in letters:
            letter_dict = parse_lifeprint_dictionary_main_page(stem + letter + ".htm")
            full_dict.update(letter_dict)
            time.sleep(sleep_time)
    except Exception as e:
        logger.info("Error in getting dictionary links:" + str(e))
    return full_dict


def parse_lifeprint_dictionary_main_page(url):
    """
    The dictionary main page contains links to subpages with words.
    Takes a url (ex. https://lifeprint.com/asl101/index/a.htm)
    Returns a dictionary with the dictionary entry as the key,
    and the link to the dictionary content page as the value
    """
    page = requests.get(url, verify=verify(), timeout=TIMEOUT_SECONDS)
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


def get_new_youtube_links_from_dictionary_content_page(
    url, dictionary_word, existing_urls, sleep_time=0.01
):
    """
    The content page contains images and videos describing the word
    Takes a url (ex. https://lifeprint.com/asl101//pages-signs/a/active.htm)
    Returns a dictionary with the url as key
    """
    time.sleep(sleep_time)
    page = requests.get(url, verify=verify(), timeout=TIMEOUT_SECONDS)
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    video_dict = {}
    for video in videos:
        url = video["src"].replace(" ", "").replace("%20", "")
        description = get_dictionary_description(video, dictionary_word)
        is_valid_link = validate_link(url, description)
        if is_valid_link and url not in existing_urls:
            value_dict = {}
            value_dict["description"] = description
            value_dict["contentSource"] = "lifeprint-dictionary"
            value_dict["contentCreator"] = "Bill Vicars"
            value_dict["contentType"] = "youtube"
            video_dict[url] = value_dict
    return video_dict


def get_links_from_vocab_page(url, description):
    link = re.sub("\.\.", "https://lifeprint.com/asl101/", url)
    page = requests.get(link, verify=verify(), timeout=TIMEOUT_SECONDS)
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    link_array = []
    for video in videos:
        link_array.append((description, video["src"]))
    return link_array


def get_lesson_page_videos(lesson_number: str, existing_urls):
    url = f"https://www.lifeprint.com/asl101/lessons/lesson{lesson_number}.htm"
    page = requests.get(url, verify=verify(), timeout=TIMEOUT_SECONDS)
    soup = BeautifulSoup(page.content, "html.parser")
    soup_links = soup.find_all("a", attrs={"href": True})
    array_of_link_tuples = []
    for link in soup_links:
        description = clean_description(str(link.contents[0] if link.contents else ""))
        href = link["href"]
        array_of_link_tuples.append((description, href))
    valid_links = find_valid_links_recursively(array_of_link_tuples)
    video_dict = {}
    for link in valid_links:
        url = link[1]
        if url not in existing_urls:
            value_dict = {}
            value_dict["description"] = link[0]
            value_dict["contentSource"] = "lifeprint-lesson-pages"
            value_dict["contentCreator"] = "Bill Vicars"
            value_dict["contentType"] = "youtube"
            video_dict[url] = value_dict
    return video_dict


def validate_link(url, description):
    if not validators.url(url):
        return False
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


def find_valid_links_recursively(links):
    exit = True
    for i, link in enumerate(links):
        if "pages-signs" in link[1]:
            links.extend(get_links_from_vocab_page(link[1], link[0]))
            exit = False
        if not validate_link(link[1], link[0]):
            del links[i]
            exit = False
    if exit:
        return links
    links = find_valid_links_recursively(links)
    return list(set(links))


def lifeprint_dictionary_to_dynamodb(
    video_dict, table_name="asl_resource_dict", dynamodb_client=None
):
    for url, item_info in video_dict.items():
        description = item_info.get("description")
        contentSource = item_info.get("contentSource")
        contentCreator = item_info.get("contentCreator")
        contentType = item_info.get("contentType")
        update_dynamodb_item(
            url=url,
            description=description,
            contentSource=contentSource,
            contentCreator=contentCreator,
            contentType=contentType,
            dynamodb_client=dynamodb_client,
            table_name=table_name,
        )


def update_dynamodb_item(
    url,
    description,
    contentSource,
    contentCreator,
    contentType,
    dynamodb_client,
    table_name,
):
    try:
        dynamodb_client.update_item(
            TableName=table_name,
            Key={"url": {"S": url}},
            UpdateExpression="set description=:d, contentSource=:s, contentCreator=:c, contentType=:t, timesPosted=:p",
            ExpressionAttributeValues={
                ":d": {"S": description},
                ":s": {"S": contentSource},
                ":c": {"S": contentCreator},
                ":t": {"S": contentType},
                ":p": {"N": "0"},
            },
            ReturnValues="UPDATED_NEW",
        )
    except Exception as e:
        logger.info(dynamodb_client)
        logger.info("Error in updating DynamoDB item:" + str(e))
        logger.info(
            {
                url: url,
                description: description,
                contentSource: contentSource,
                contentCreator: contentCreator,
                contentType: contentType,
            }
        )


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
    full_description = (
        dictionary_word + " | " + raw_description
        if raw_description != ""
        else dictionary_word
    )
    description = clean_description(full_description)
    return description


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


def clean_dictionary_word(word):
    word = word.replace("\n", "")
    word = word.replace(" ", "")
    word = word.replace('"', "")
    return word


def query_dynamodb_by_key(key, dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    response = table.query(KeyConditionExpression=Key("url").eq(key))
    return response["Items"]


def delete_dynamodb_by_key(key, dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    response = table.delete_item(Key={"url": key})
    return response


def dynamodb_scan(dynamodb_resource, table_name):
    table = dynamodb_resource.Table(table_name)
    scan = table.scan()
    return scan["Items"]


def load_creds_env_gather():
    creds = {}
    creds["AWS_REGION"] = os.environ["AWS_REGION"]
    creds["AWS_ACCESS_KEY_ID"] = os.environ["AWS_ACCESS_KEY_ID"]
    creds["AWS_SECRET_ACCESS_KEY"] = os.environ["AWS_SECRET_ACCESS_KEY"]
    return creds

