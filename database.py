import hashlib
import secrets
from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")

# Database
db = client["product_recommendation_db"]

# Collections
products_collection = db["products"]
users_collection = db["users"]
interactions_collection = db["interactions"]


# Insert products
def save_products(products):

    products_collection.delete_many({})

    records = products.drop(
        columns=["features"],
        errors="ignore"
    ).to_dict("records")

    if records:
        products_collection.insert_many(records)


# Save user activity
def save_interaction(user_id, product_name, action):

    data = {
        "user_id": user_id,
        "product_name": product_name,
        "action": action,
        "timestamp": datetime.now()
    }

    interactions_collection.insert_one(data)


# Get interaction history
def get_user_history(user_id):

    return list(
        interactions_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        )
    )

def get_recommendations_from_history(user_id):

    history = list(
        interactions_collection.find(
            {
                "user_id": user_id,
                "action": "view"
            }
        ).sort("timestamp", -1)
    )

    viewed_products = []

    for item in history:
        name = item["product_name"]

        if name not in viewed_products:
            viewed_products.append(name)

    return viewed_products

def register_user(username, password):

    if users_collection.find_one({"username": username}):
        return False, "Username already exists."

    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        200000
    ).hex()

    users_collection.insert_one({
        "username": username,
        "salt": salt,
        "password_hash": password_hash
    })

    return True, "Registration successful!"


def login_user(username, password):

    user = users_collection.find_one({
        "username": username
    })

    if not user:
        return False

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(user["salt"]),
        200000
    ).hex()

    return secrets.compare_digest(
        password_hash,
        user["password_hash"]
    )

def get_all_interactions():

    interactions = list(
        interactions_collection.find(
            {"action": "view"},
            {
                "_id": 0,
                "user_id": 1,
                "product_name": 1
            }
        )
    )

    return interactions
reviews_collection = db["reviews"]

def save_review(user_id, product_name, rating, review):
    reviews_collection.update_one(
        {
            "user_id": user_id,
            "product_name": product_name
        },
        {
            "$set": {
                "rating": rating,
                "review": review,
                "timestamp": datetime.now()
            }
        },
        upsert=True
    )


def get_product_reviews(product_name):
    return list(
        reviews_collection.find(
            {"product_name": product_name},
            {"_id": 0}
        )
    )