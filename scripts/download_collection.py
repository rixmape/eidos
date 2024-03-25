"""
This module is used to download the collection from the Firestore database.
"""

import json

import firebase_admin
import toml
from firebase_admin import credentials, firestore

with open(".streamlit/secrets.toml", "r") as f:
    secrets = toml.load(f)

certificate = dict(secrets["firebase"])
credential = credentials.Certificate(certificate)
firebase_admin.initialize_app(credential)

firestore_client = firestore.client()
database = firestore_client.collection("user_feedback").stream()

feedback = {}
for doc in database:
    data = doc.to_dict()

    # Convert the timestamp to a string
    data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    # Convert `messages.content` to a dictionary
    messages = data["messages"]
    for message in messages:
        message["content"] = json.loads(message["content"])

    feedback[doc.id] = data

with open("feedback.json", "w") as f:
    json.dump(feedback, f, indent=4)

print("Collection downloaded successfully.")
