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

# ============ USER MANAGEMENT FUNCTIONS ============

def get_or_create_user(user_id):
    """Fetch or create a user in Firebase Firestore."""
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        # Create a new user with default fields
        user_data = {
            "user_id": user_id,
            "chat_history": [],
            "important_info": [],
            "incognito_mode": False,
        }
        user_ref.set(user_data)
        return user_data
    return user_doc.to_dict()

def get_chat_history(user_id):
    """Retrieve the chat history of a user."""
    user = get_or_create_user(user_id)
    return user.get("chat_history", [])

def get_chat_history_from_subcollection(user_id, limit=10):
    """Retrieve chat messages from subcollection (alternative approach)."""
    docs = (
        db.collection("users")
        .document(user_id)
        .collection("messages")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]

def toggle_incognito_mode(user_id):
    """Toggle incognito mode for the user."""
    user = get_or_create_user(user_id)
    new_status = not user.get("incognito_mode", False)
    
    db.collection("users").document(user_id).update({
        "incognito_mode": new_status
    })
    
    return f"Incognito mode is now {'ON' if new_status else 'OFF'}."

def save_user_info(user_id, name=None, age=None, location=None, phone=None, friends=None, college=None):
    """Store or update user details in Firebase."""
    user_ref = db.collection("users").document(user_id)
    
    # Get existing data to preserve other fields
    existing_data = user_ref.get().to_dict()
    if existing_data is None:
        existing_data = {}
    
    update_data = {}
    if name: update_data["name"] = name
    if age: update_data["age"] = age
    if college: update_data["college"] = college
    if location: update_data["location"] = location
    if phone: update_data["phone"] = phone
    if friends: update_data["friends"] = friends
    
    # Merge with existing data
    updated_data = {**existing_data, **update_data}
    user_ref.set(updated_data)

def extract_keywords(text):
    """Extracts important keywords (names, places, events) from text."""
    import re
    keywords = re.findall(r"\b[A-Z][a-z]+\b", text)  # Detect capitalized words
    return list(set(keywords))

def save_message(user_id, role, content, emotion=None):
    """Save messages to Firebase (main document with subcollection)."""
    user = get_or_create_user(user_id)  # Ensure user exists
    
    # Check if incognito mode is enabled
    if user.get("incognito_mode", False):
        return  # Skip saving messages when incognito mode is enabled

    chat_history = user.get("chat_history", [])
    important_info = user.get("important_info", [])

    # Extract & store important keywords
    keywords = extract_keywords(content)
    important_info.extend([kw for kw in keywords if kw not in important_info])

    # Create message entry
    message_entry = {
        "role": role,
        "content": content,
        "emotion": emotion,
        "timestamp": firestore.SERVER_TIMESTAMP
    }

    # Append to chat history array (limited to 50 messages)
    chat_history.append({"role": role, "content": content, "emotion": emotion})
    if len(chat_history) > 50:
        chat_history = chat_history[-50:]

    # Also save to subcollection for better querying
    db.collection("users").document(user_id).collection("messages").add({
        "role": role,
        "content": content,
        "emotion": emotion,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    # Update user document
    db.collection("users").document(user_id).update({
        "chat_history": chat_history,
        "important_info": important_info
    })

def get_user_info(user_id):
    """Get all user information."""
    user = get_or_create_user(user_id)
    return user

# ============ LEGACY FUNCTIONS (for compatibility) ============

def save_message_old(user_id, text, emotion=None):
    """Legacy function - saves message to subcollection only."""
    db.collection("users") \
      .document(user_id) \
      .collection("messages") \
      .add({
          "text": text,
          "emotion": emotion,
          "timestamp": firestore.SERVER_TIMESTAMP
      })

def get_messages_old(user_id, limit=10):
    """Legacy function - retrieves messages from subcollection."""
    docs = (
        db.collection("users")
        .document(user_id)
        .collection("messages")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]

# ============ ADDITIONAL HELPER FUNCTIONS ============

def delete_user(user_id):
    """Delete a user and all their data."""
    # Delete subcollection messages
    messages_ref = db.collection("users").document(user_id).collection("messages")
    for doc in messages_ref.stream():
        doc.reference.delete()
    
    # Delete user document
    db.collection("users").document(user_id).delete()

def get_all_users():
    """Get all users (for admin purposes)."""
    users = []
    for doc in db.collection("users").stream():
        users.append(doc.to_dict())
    return users

def search_messages(user_id, query):
    """Search through user's messages."""
    messages = get_chat_history_from_subcollection(user_id, limit=100)
    results = []
    for msg in messages:
        if query.lower() in msg.get("content", "").lower():
            results.append(msg)
    return results
