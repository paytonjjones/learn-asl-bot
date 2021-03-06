from unittest import mock
from unittest.mock import patch
import dotenv
import pytest
import logging
from gather.src.handler import lambda_gather

try:
    dotenv.load_dotenv()
except:
    pass
logger = logging.getLogger()
logger.setLevel(logging.INFO)

mock_dictionary_links = {
    "A": "https://lifeprint.com/asl101/index/a.htm",
    "B": "https://lifeprint.com/asl101/index/b.htm",
}

contentUrl1 = "https://www.youtube.com/embed/2?rel=0&autoplay=1"
contentUrl2 = "https://www.youtube.com/embed/1?rel=0&autoplay=1"
contentUrl3 = "https://www.youtube.com/embed/3?rel=0&autoplay=1"
contentUrl4 = "https://www.youtube.com/embed/4?rel=0&autoplay=1"

mock_content_entries = {
    contentUrl1: {
        "description": 'ACTIVE | "DO" / DOING / "I was doing..."If you are describing a situation or telling a story in which you want to indicate that general action was taking place, then here is a general version of "DO."\xa0 General activity can be shown with this sign.\xa0You hold your hands out in front of you and move...',
        "contentSource": "lifeprint-dictionary",
        "contentCreator": "Bill Vicars",
        "contentType": "youtube",
    },
    contentUrl2: {
        "description": "A test description",
        "contentSource": "lifeprint-dictionary",
        "contentCreator": "Bill Vicars",
        "contentType": "youtube",
    },
}

mock_content_entries_lessons = {
    contentUrl1: {
        "description": "A SENTENCE FROM A LESSON",
        "contentSource": "lifeprint-lesson-pages",
        "contentCreator": "Bill Vicars",
        "contentType": "youtube",
    },
    contentUrl2: {
        "description": "A DIFFERENT SENTENCE FROM A LESSON",
        "contentSource": "lifeprint-lesson-pages",
        "contentCreator": "Bill Vicars",
        "contentType": "youtube",
    },
}


@pytest.mark.unit
@patch("gather.src.handler.dynamodb_scan")
@patch("gather.src.handler.get_lifeprint_dictionary_links")
@patch("gather.src.handler.get_new_youtube_links_from_dictionary_content_page")
@patch("gather.src.handler.lifeprint_dictionary_to_dynamodb")
@patch("gather.src.handler.boto3.client")
@patch("gather.src.handler.update_dynamodb_item")
@patch("gather.src.handler.get_lesson_page_videos")
def test_lambda_gather(
    get_lesson_page_videos_mock,
    update_dynamodb_item_mock,
    boto3_client_mock,
    lifeprint_dictionary_to_dynamodb_mock,
    get_new_youtube_links_from_dictionary_content_page_mock,
    get_lifeprint_dictionary_links_mock,
    saved_entries_mock,
):
    get_lesson_page_videos_mock.return_value = mock_content_entries_lessons
    update_dynamodb_item_mock.return_value = None
    get_lifeprint_dictionary_links_mock.return_value = mock_dictionary_links
    get_new_youtube_links_from_dictionary_content_page_mock.return_value = (
        mock_content_entries
    )
    lifeprint_dictionary_to_dynamodb_mock.return_value = None
    boto3_client_mock.return_value = "mock_boto3_client"
    saved_youtube_links = ["https://www.youtube.com/foo", "https://www.youtube.com/bar"]
    saved_entries_mock.return_value = [
        {"url": saved_youtube_links[0]},
        {"url": saved_youtube_links[1]},
    ]

    lambda_gather({}, None)

    logger.info(get_new_youtube_links_from_dictionary_content_page_mock)
    get_lifeprint_dictionary_links_mock.assert_called_once()
    get_new_youtube_links_from_dictionary_content_page_mock.assert_has_calls(
        [
            mock.call(
                "https://lifeprint.com/asl101/index/a.htm", "A", saved_youtube_links
            ),
            mock.call(
                "https://lifeprint.com/asl101/index/b.htm", "B", saved_youtube_links
            ),
        ]
    )
    get_lesson_page_videos_mock.assert_called()
    lifeprint_dictionary_to_dynamodb_mock.assert_has_calls(
        [
            mock.call(mock_content_entries, "asl_resource_dict", "mock_boto3_client"),
            mock.call(
                mock_content_entries_lessons, "asl_resource_dict", "mock_boto3_client"
            ),
        ]
    )

    update_dynamodb_item_mock.assert_called()
