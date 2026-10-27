from pymongo import MongoClient
import os

from dotenv import load_dotenv


load_dotenv()

uri = os.getenv("MONGODB_URI")

client = MongoClient(uri)

try:
    client.admin.command("ping")
    print("MongoDB connection successful!")
except Exception as e:
    print("MongoDB connection failed:")
    print(e)
finally:
    client.close()