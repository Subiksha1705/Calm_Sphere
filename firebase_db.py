import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---------- DB FUNCTIONS ----------

def save_message(user_id, text, emotion=None):
    db.collection("users") \
      .document(user_id) \
      .collection("messages") \
      .add({
          "text": text,
          "emotion": emotion,
          "timestamp": firestore.SERVER_TIMESTAMP
      })

def get_messages(user_id, limit=10):
    docs = (
        db.collection("users")
        .document(user_id)
        .collection("messages")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]
