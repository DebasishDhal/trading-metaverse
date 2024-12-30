# import pymongo
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
#From this env file .env, read mongodb user and password
mongodb_username = os.getenv("MONGODB_USERNAME")
mongodb_password = os.getenv("MONGODB_PASSWORD")

def get_mongo_client():
    # print("confirmation mongo_utils")
    try:
        mongo_client = MongoClient(
                                    host = "mongodb://mongodb-metaverse:27017/",
                                   username = mongodb_username,
                                   password = mongodb_password,
                                   authSource='admin',
                                    )
        print("MongoDB connection successful")
        return mongo_client
    except Exception as e:
        print(e)
        return None

mongo_client = get_mongo_client()    