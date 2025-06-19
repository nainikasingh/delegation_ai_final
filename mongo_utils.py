from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["delegation"]

def get_user_by_id(user_id):
    return db["users"].find_one({"_id": ObjectId(user_id)})

def get_all_tasks():
    return list(db["tasks"].find())

def get_role_hierarchy(role):
    hierarchy = {"Boss": 3, "Delegator": 2, "Delegatee": 1}
    return hierarchy.get(role.capitalize(), 1)
