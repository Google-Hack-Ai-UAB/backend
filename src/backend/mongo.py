from pymongo import MongoClient


def init_mongo():
    """Init a mongo instance"""
    username = "root"
    password = "example"
    host = "mongo"
    port = 27017
    auth_source = "admin"  # Authentication database
    return MongoClient(
        host, port, username=username, password=password, authSource=auth_source
    )
