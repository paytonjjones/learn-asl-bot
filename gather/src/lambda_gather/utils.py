import logging
import time
import requests
import re

from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def parse_entire_dictionary():
    stem = "https://lifeprint.com/asl101/index/"
    full_dict = {}
    for letter in "abcdefghijklmnopqrstuvwxyz":  #
        letter_dict = parse_dictionary_main_page(stem + letter + ".htm")
        full_dict.update(letter_dict)
        time.sleep(0.5)
    return full_dict


def parse_dictionary_main_page(url):
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
        text = blob.text
        link = blob.get("href")
        link = re.sub("\.\.", "https://lifeprint.com/asl101/", link)
        master_dict[text] = link
    return master_dict
