import os
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

# Import Firebase database functions
from firebase_db import (
    get_or_create_user,
    get_chat_history,
    toggle_incognito_mode,
    save_user_info,
    save_message,
    get_user_info,
    search_messages
)

# Initialize InferenceClient (cloud inference)
client = InferenceClient(api_key=HUGGING_FACE_API_KEY)

# Emotion detection pipeline
emotion_detector = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

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
    name = user.get("name", "friend")

    # Greeting message if it's the first message after login
    if len(chat_history) == 0:
        return f"Hey {name}! Great to see you again! How have you been?"

    # System message for AI
    system_message = {
        "role": "system",
        "content": (
            "You are Calm, a friendly and empathetic chatbot supporting emotional well-being. "
            "You provide short and thoughtful responses like a caring friend. "
            f"You remember the user's key details like name ({name}), age, college, friends, and location. "
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
        
        # Save messages to Firebase
        save_message(user_id, "user", user_message, emotion)
        save_message(user_id, "assistant", answer)
        
        return answer
    except Exception as e:
        return "Sorry, I ran into an issue. Let's try again!"
