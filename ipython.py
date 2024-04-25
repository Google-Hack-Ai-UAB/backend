import csv

import pymongo
from bson.objectid import ObjectId

MONGO_URL = "mongodb+srv://userstorer:youwillneverguessthispassword@aihack.89so8jl.mongodb.net/?retryWrites=true&w=majority&appName=AIHack"

client = pymongo.MongoClient(MONGO_URL)
db = client["ai"]
collection = db["jobs"]

collection.find_one()
