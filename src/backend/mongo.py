import logging
import os
from typing import Optional

from pymongo import MongoClient

LOG = logging.getLogger(__name__)


def init_mongo():
    """Init a mongo instance"""
    LOG.debug(f"Connection using url: {os.getenv('MONGO_URL')}")
    return MongoClient(os.getenv("MONGO_URL"))


def get_cursor(db: str, collection: Optional[str] = None):
    client = init_mongo()
    return client[db] if not collection else client[db][collection]
