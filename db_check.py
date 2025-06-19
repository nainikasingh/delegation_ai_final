from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "delegation"

def print_sample_from_collection(db, collection_name, limit=3):
    if collection_name in db.list_collection_names():
        print(f"\n📄 Sample from collection: {collection_name}")
        docs = list(db[collection_name].find().limit(limit))
        if not docs:
            print("⚠️  Collection exists but is empty.")
        for doc in docs:
            pprint(doc)
    else:
        print(f"❌ Collection '{collection_name}' not found.")

def main():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]

        print(f"✅ Connected to database: {DB_NAME}")
        print("📁 Collections found:", db.list_collection_names())

        # Try both lowercase and similar variants
        print_sample_from_collection(db, "users")
        print_sample_from_collection(db, "tasks")
        print_sample_from_collection(db, "user")  # Just in case

        client.close()
    except Exception as e:
        print("❌ MongoDB connection failed:", str(e))

if __name__ == "__main__":
    main()
