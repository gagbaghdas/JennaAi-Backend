from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_DB_CONNECTION_STRING"))
db = client[os.getenv("DB_NAME")]
