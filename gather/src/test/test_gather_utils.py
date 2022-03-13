import dotenv
import pytest
import logging
import boto3
import os
import requests
from bs4 import BeautifulSoup


dotenv.load_dotenv()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


from gather.src.lambda_gather.utils import (
    clean_description,
    clean_dictionary_word,
    delete_dynamodb_by_key,
    get_dictionary_description,
    get_lifeprint_dictionary_links,
    get_new_youtube_links_from_dictionary_content_page,
    lifeprint_dictionary_to_dynamodb,
    parse_lifeprint_dictionary_main_page,
    query_dynamodb_by_key,
    smart_truncate,
    update_dynamodb_item,
)


# from post.src.lambda_post.utils import load_creds_env, post_youtube, smart_truncate


@pytest.mark.integration
def test_get_lifeprint_dictionary_links():
    lifeprint_dictionary_pages = get_lifeprint_dictionary_links(0.01, "bc")
    assert len(lifeprint_dictionary_pages) > 0
    for key, value in lifeprint_dictionary_pages.items():
        assert isinstance(key, str)
        assert value.startswith("https://lifeprint.com/asl101/")


@pytest.mark.integration
def test_parse_lifeprint_dictionary_main_page():
    test_url = "https://lifeprint.com/asl101/index/y.htm"
    actual = parse_lifeprint_dictionary_main_page(test_url)
    assert len(actual) > 0
    for key, value in actual.items():
        assert isinstance(key, str)
        assert value.startswith("https://lifeprint.com/asl101/")


@pytest.mark.integration
def test_get_new_youtube_links_from_dictionary_content_page():
    test_url = "https://lifeprint.com/asl101//pages-signs/a/active.htm"
    actual = get_new_youtube_links_from_dictionary_content_page(test_url, "ACTIVE", [])
    assert len(actual) > 0
    expectedText = 'ACTIVE | "DO" / DOING / "I was doing..."'
    expectedVideoLink = "https://www.youtube.com/embed/8ZBfz7-5w54?rel=0&autoplay=1"
    assert expectedVideoLink in actual.keys()
    do_doing = actual[expectedVideoLink]
    assert expectedText in do_doing["description"]
    assert do_doing["contentSource"] == "lifeprint-dictionary"
    assert do_doing["contentCreator"] == "Bill Vicars"
    assert do_doing["contentType"] == "youtube"


@pytest.mark.integration
def test_lifeprint_dictionary_to_dynamodb():
    contentUrl = "https://www.fakeurl.com"
    test_video_dict = {
        contentUrl: {
            "description": 'ACTIVE | "DO" / DOING / "I was doing..."If you are describing a situation or telling a story in which you want to indicate that general action was taking place, then here is a general version of "DO."\xa0 General activity can be shown with this sign.\xa0You hold your hands out in front of you and move...',
            "contentSource": "lifeprint-dictionary",
            "contentCreator": "Bill Vicars",
            "contentType": "youtube",
        },
    }
    dynamodb_client = boto3.client(
        "dynamodb", region_name=os.environ["AWS_REGION"], verify=False
    )
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name=os.environ["AWS_REGION"], verify=False
    )

    lifeprint_dictionary_to_dynamodb(
        test_video_dict, "asl_resource_dict", dynamodb_client
    )
    actual = query_dynamodb_by_key(contentUrl, dynamodb_resource, "asl_resource_dict",)[
        0
    ]
    print("OK HERE DUMMY")
    print(actual)
    assert actual["contentCreator"] == test_video_dict[contentUrl]["contentCreator"]
    assert actual["description"] == test_video_dict[contentUrl]["description"]
    assert actual["contentType"] == test_video_dict[contentUrl]["contentType"]
    assert actual["contentSource"] == test_video_dict[contentUrl]["contentSource"]
    assert actual["url"] == contentUrl

    delete_dynamodb_by_key(contentUrl, dynamodb_resource, "asl_resource_dict")


@pytest.mark.integration
def test_update_dynamodb_item():
    contentUrl = "https://test.url"
    test_video_dict = {
        "url": contentUrl,
        "description": "A description",
        "contentSource": "test-source",
        "contentCreator": "Test Creator",
        "contentType": "youtube",
    }
    dynamodb_client = boto3.client(
        "dynamodb", region_name=os.environ["AWS_REGION"], verify=False
    )
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name=os.environ["AWS_REGION"], verify=False
    )

    update_dynamodb_item(
        url=test_video_dict["url"],
        description=test_video_dict["description"],
        contentSource=test_video_dict.get("contentSource", ""),
        contentCreator=test_video_dict.get("contentCreator", ""),
        contentType=test_video_dict.get("contentType", ""),
        dynamodb_client=dynamodb_client,
        table_name="asl_resource_dict",
    )

    actual = query_dynamodb_by_key(contentUrl, dynamodb_resource, "asl_resource_dict",)[
        0
    ]
    assert actual["url"] == test_video_dict["url"]
    assert actual["contentCreator"] == test_video_dict["contentCreator"]
    assert actual["description"] == test_video_dict["description"]
    assert actual["contentType"] == test_video_dict["contentType"]
    assert actual["contentSource"] == test_video_dict["contentSource"]

    delete_dynamodb_by_key(contentUrl, dynamodb_resource, "asl_resource_dict")


@pytest.mark.integration
def test_get_dictionary_description():
    test_url = "https://lifeprint.com/asl101//pages-signs/a/active.htm"
    page = requests.get(test_url, verify=False, timeout=5)
    soup = BeautifulSoup(page.content, "html.parser")
    videos = soup.find_all("iframe")
    test_video = videos[0]
    actual = get_dictionary_description(test_video, "ACTIVE")
    expectedText = 'ACTIVE | "DO" / DOING / "I was doing..."'
    assert expectedText in actual
    assert len(expectedText) <= 300


@pytest.mark.unit
def test_clean_description():
    test_text = '     \n\tACTIVE    | "DO" / DOING / "I was doing..."'
    actual = clean_description(test_text)
    assert actual == 'ACTIVE | "DO" / DOING / "I was doing..."'


@pytest.mark.unit
def test_smart_truncate():
    content1 = "This is a test of the smart_truncate function"
    content2 = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede."
    expectedContent2 = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec..."
    actualContent1 = smart_truncate(content1)
    actualContent2 = smart_truncate(content2)
    assert actualContent1 == content1
    assert actualContent2 == expectedContent2


@pytest.mark.unit
def test_clean_dictionary_word():
    assert clean_dictionary_word("a") == "a"
    assert clean_dictionary_word("\na") == "a"
    assert clean_dictionary_word("a b") == "ab"
    assert clean_dictionary_word('"a"') == "a"

