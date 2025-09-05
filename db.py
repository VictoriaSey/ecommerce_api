from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# connect to mongo atlas cluster
mongo_client = MongoClient(os.getenv("MONGO_URI"))


# Access database
ecommerce_api_db = mongo_client["ecommerce_api_db"]

# Pick a connection to operate on
products_collection = ecommerce_api_db["products"]
users_collection = ecommerce_api_db["users"]
carts_collection = ecommerce_api_db["carts"]