import os
import pymongo
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from transformers import pipeline
import asyncio

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Load environment variables
load_dotenv()
HUGGING_FACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Initialize MongoDB
client_mongo = pymongo.MongoClient(MONGO_URI)
db = client_mongo["chatbot_db"]
users_collection = db["users"]

# Initialize InferenceClient (cloud inference)
client = InferenceClient(api_key=HUGGING_FACE_API_KEY)

# Emotion detection pipeline
emotion_detector = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

def get_or_create_user(user_id):
    """Fetch or create a user in MongoDB."""
    user = users_collection.find_one({"user_id": user_id})

    if not user:
        # Create a new user with default fields
        user_data = {
            "user_id": user_id,
            "chat_history": [],
            "important_info": [],
        }
        users_collection.insert_one(user_data)
        return user_data
    return user

def get_chat_history(user_id):
    """Retrieve the chat history of a user."""
    user = get_or_create_user(user_id)
    return user.get("chat_history", [])

def toggle_incognito_mode(user_id):
    """Toggle incognito mode for the user."""
    user = get_or_create_user(user_id)
    new_status = not user.get("incognito_mode", False)
    
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"incognito_mode": new_status}},
        upsert=True
    )
    
    return f"Incognito mode is now {'ON' if new_status else 'OFF'}."

def save_user_info(user_id, name=None, age=None, location=None, phone=None, friends=None):
    """Store or update user details in MongoDB."""
    update_data = {}
    if name: update_data["name"] = name
    if age: update_data["age"] = age
    if location: update_data["location"] = location
    if phone: update_data["phone"] = phone
    if friends: update_data["friends"] = friends

    users_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )

def extract_keywords(text):
    """Extracts important keywords (names, places, events) from text."""
    keywords = re.findall(r"\b[A-Z][a-z]+\b", text)  # Detect capitalized words (possible names/places)
    return list(set(keywords))  # Remove duplicates

def save_message(user_id, role, content):
    """Save messages to MongoDB only if incognito mode is OFF."""
    user = get_or_create_user(user_id)  # Ensure user exists
    
    # Check if incognito mode is enabled
    if user.get("incognito_mode", False):
        return  # Skip saving messages when incognito mode is enabled

    chat_history = user.get("chat_history", [])
    important_info = user.get("important_info", [])

    # Extract & store important keywords before old messages are deleted
    keywords = extract_keywords(content)
    important_info.extend([kw for kw in keywords if kw not in important_info])  # Avoid duplicates

    # Append new message
    chat_history.append({"role": role, "content": content})

    # Limit chat history to last 50 messages
    if len(chat_history) > 50:
        chat_history = chat_history[-50:]

    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"chat_history": chat_history, "important_info": important_info}},
        upsert=True
    )

def detect_emotion(text):
    """Detect the primary emotion in user input."""
    result = emotion_detector(text)[0]
    return result["label"]

def get_chatbot_response(user_id, user_message):
    """Generate chatbot response while remembering key user details."""
    
    user = get_or_create_user(user_id)  # Ensure user exists
    
    emotion = detect_emotion(user_message)
    
    # Retrieve chat history and important info
    chat_history = user.get("chat_history", [])[-6:]  # Last 6 messages for context
    important_info = user.get("important_info", [])

    # Greeting message if it's the first message after login
    if len(chat_history) == 0:
        name = user.get("name", "friend")
        return f"Hey {name}! Great to see you again! How have you been?"

    # System message for AI
    system_message = {
        "role": "system",
        "content": (
            "You are Calm, a friendly and empathetic chatbot supporting emotional well-being. "
            "You provide short and thoughtful responses like a caring friend. "
            "You remember the user's key details like name, age, college, friends, and location. "
            "You also remember key words from past conversations. "
            "If the user is in serious distress, slowly guide them towards professional help. "
            "Only provide helpline numbers if the user is truly in danger."
            "Never answer to unrelated topics. Your only job is to talk to the user like a true friend, not to help with other tasks. "
            "If the user asks something unrelated, divert the topic back to mental health and feelings without the user noticing."
            "The user should feel safe and comfortable talking to you."
            "if the user asks to do any task or give something you should say that you are not capable of doing that and you are a mental health bot"
            "Never ever respond to other topic simply say Your going off topic if the user repeteadly asks same question"
            "divert the topic back to mental health and feelings without the user noticing."
            "Never do other work for the user your prime goal is to make the user feel happy dont pry into users life dont ask so many questions"
        )
    }
    
    # Compile conversation context
    conversation = [system_message] + chat_history + [{"role": "user", "content": user_message}]
    
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct",
            messages=conversation,
            max_tokens=200
        )
        answer = completion.choices[0].message.content
        
        # Save messages to DB
        save_message(user_id, "user", user_message)
        save_message(user_id, "assistant", answer)
        
        return answer
    except Exception as e:
        return "Sorry, I ran into an issue. Let's try again!"