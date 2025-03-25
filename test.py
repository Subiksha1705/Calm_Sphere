import pymongo
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client["chatbot_db"]
    print("✅ Connected to MongoDB!")
except Exception as e:
    print("❌ MongoDB Connection Failed:", e)
