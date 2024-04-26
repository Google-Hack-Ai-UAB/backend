# STL
import os
import logging

# PDM
from dotenv import load_dotenv

# LOCAL
from src.backend.mongo import get_cursor

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(__name__)

load_dotenv()


def test_mongo_url():
    assert os.getenv("MONGO_URL") is not None


def test_mongo_connection():
    cursor = get_cursor("ai", "users")
    assert cursor is not None


def test_mongo_query():
    cursor = get_cursor("ai", "users")
    result = cursor.find_one()
    LOG.info(f"Result: {result}")
    assert result
