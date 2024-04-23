import os

from pymongo import MongoClient


def init_mongo():
    """Init a mongo instance"""
    return MongoClient(url=os.getenv("MONGO_URL"))
