from unittest.mock import Mock, patch
import dotenv
import pytest
import boto3

try:
    dotenv.load_dotenv()
except:
    pass

from post.src.lambda_post.utils import (
    load_creds_env,
    post_from_dynamodb,
    post_youtube,
    smart_truncate,
    verify,
)


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
@patch("post.src.lambda_post.utils.load_creds_env")
@patch("post.src.lambda_post.utils.praw")
@patch("post.src.lambda_post.utils.requests")
def test_post_youtube(requests, praw, load_creds_env):
    content_dict = {
        "description": "WORD | A description",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }
    reddit_creds = {
        "CLIENT_ID": "CLIENT_ID",
        "CLIENT_SECRET": "CLIENT_SECRET",
        "USERNAME": "USERNAME",
        "PASSWORD": "PASSWORD",
    }
    post_youtube(content_dict, reddit_creds)
    praw.Reddit.assert_called_with(
        user_agent="test",
        client_id=reddit_creds["CLIENT_ID"],
        client_secret=reddit_creds["CLIENT_SECRET"],
        username=reddit_creds["USERNAME"],
        password=reddit_creds["PASSWORD"],
        requestor_kwargs={"session": requests.Session()},
    )
    praw.Reddit.return_value.subreddit.return_value.submit.assert_called_with(
        title="WORD | A description", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )


@pytest.mark.integration
def test_load_creds_env():
    creds = load_creds_env()
    assert isinstance(creds["CLIENT_ID"], str)
    assert isinstance(creds["USERNAME"], str)
    assert isinstance(creds["CLIENT_SECRET"], str)
    assert isinstance(creds["PASSWORD"], str)
    assert isinstance(creds["AWS_REGION"], str)
    assert isinstance(creds["DYNAMODB_TABLE_NAME"], str)


@pytest.mark.integration
@patch("post.src.lambda_post.utils.post_youtube")
def test_post_from_dynamo_db(post_youtube):
    creds = load_creds_env()
    dynamodb_table_name = creds["DYNAMODB_TABLE_NAME"]
    dynamodb_resource = boto3.resource(
        "dynamodb", region_name=creds["AWS_REGION"], verify=verify()
    )
    dynamodb_client = Mock()

    post_from_dynamodb(creds, dynamodb_resource, dynamodb_client, dynamodb_table_name)
    assert isinstance(post_youtube.call_args[0][0]["url"], str)
    assert isinstance(post_youtube.call_args[0][0]["description"], str)
    dynamodb_client.update_item.assert_called_once()

