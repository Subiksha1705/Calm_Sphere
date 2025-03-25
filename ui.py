import torch
import asyncio
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from intro import get_chatbot_response, get_or_create_user, save_user_info, save_message, get_chat_history
import warnings

warnings.simplefilter("ignore", category=FutureWarning)

# ✅ Fix asyncio event loop issue for Windows
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# ✅ Page Config with Theming
st.set_page_config(page_title="Calm Sphere", layout="wide")
st.markdown("""
    <style>
        body { background-color: #eef2f3; }
        .stChatMessage { border-radius: 15px; padding: 10px; margin: 5px 0; }
        .stChatMessage.user { background-color: #b3e5fc; }
        .stChatMessage.assistant { background-color: #ffccbc; }
        .sidebar-content { padding: 20px; }
        .stButton>button { border-radius: 10px; padding: 8px 15px; }
        .stTextInput>div>div>input { border-radius: 10px; padding: 10px; }
        .stMarkdown { font-size: 18px; }
        .stTitle { color: #37474f; }
        .stSubheader { color: #455a64; }
    </style>
""", unsafe_allow_html=True)

# ✅ Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_details" not in st.session_state:
    st.session_state.user_details = {}
if "analysis_option" not in st.session_state:
    st.session_state.analysis_option = "None"
if "gratitude_entries" not in st.session_state:
    st.session_state.gratitude_entries = []

# ✅ User Login
if st.session_state.user_id is None:
    st.title("🤗 Calm Sphere - Your Mental Health Friend")
    st.subheader("User Registration/Login")
    user_id = st.text_input("Enter your username:")

    if user_id:
        user = get_or_create_user(user_id)
        if not user:
            st.subheader("Register Your Details")
            name = st.text_input("Your Name:")
            age = st.text_input("Your Age:")
            college = st.text_input("Your College:")
            location = st.text_input("Your Location:")

            if st.button("Save Details"):
                if name and age and college and location:
                    save_user_info(user_id, name, age, college, location)
                    st.session_state.user_id = user_id
                    st.success(f"Welcome {name}! Start chatting now.")
                    st.rerun()
                else:
                    st.error("Please fill in all details.")
        else:
            st.session_state.user_id = user_id
            st.session_state.chat_history = user.get("chat_history", [])
            st.success(f"Welcome back, {user.get('name', 'friend')}!")
            st.rerun()

# ✅ Sidebar with Enhanced UI
if st.session_state.user_id:
    with st.sidebar:
        st.image("calmsphere_logo.png", width=150)
        st.title("🌿 Calm Sphere")
        
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

        st.session_state.analysis_option = st.radio("View Analysis:",
                                                     ["None", "Mood Analysis", "Word Cloud", "Sentiment Distribution"],
                                                     index=["None", "Mood Analysis", "Word Cloud", "Sentiment Distribution"].index(st.session_state.analysis_option))

# ✅ Chat Interface with Stylish Chat Bubbles
if st.session_state.user_id:
    st.subheader("💬 Chat with Calm Sphere")

    # ✅ Display Previous Messages
    chat_history = get_chat_history(st.session_state.user_id)
    
    for chat in chat_history:
        role = "🤛 You" if chat["role"] == "user" else "🤖 Calm Sphere"
        with st.chat_message(chat["role"]):
            st.markdown(f"**{role}**\n\n{chat['content']}")

    # ✅ Handle New User Input
    user_input = st.chat_input("Type your message...")
    if user_input:
        # Display User Message
        with st.chat_message("user"):
            st.markdown(f"**🤛 You**\n\n{user_input}")

        # Generate Response
        with st.spinner("Thinking..."):
            response = get_chatbot_response(st.session_state.user_id, user_input)

        # ✅ Save Messages
        save_message(st.session_state.user_id, "user", user_input)
        save_message(st.session_state.user_id, "assistant", response)

        # Display Assistant Message
        with st.chat_message("assistant"):
            st.markdown(f"**🤖 Calm Sphere**\n\n{response}")

# ✅ Analysis Section with Improved Layout
if st.session_state.user_id and st.session_state.analysis_option != "None":
    st.subheader(f"📊 {st.session_state.analysis_option}")

    if st.session_state.analysis_option == "Mood Analysis":
        mood_data = pd.DataFrame({"Time": list(range(len(st.session_state.chat_history))),
                                  "Mood Score": [1 if "happy" in msg["content"] else -1 for msg in st.session_state.chat_history]})
        st.line_chart(mood_data.set_index("Time"))

    elif st.session_state.analysis_option == "Word Cloud":
        text = " ".join(msg["content"] for msg in st.session_state.chat_history)
        wordcloud = WordCloud(width=600, height=300, background_color="white").generate(text)
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    elif st.session_state.analysis_option == "Sentiment Distribution":
        sentiment_data = pd.DataFrame({"Sentiment": ["Positive", "Negative", "Neutral"],
                                       "Count": [sum(1 for msg in st.session_state.chat_history if "happy" in msg["content"]),
                                                  sum(1 for msg in st.session_state.chat_history if "sad" in msg["content"]),
                                                  len(st.session_state.chat_history)]})
        st.bar_chart(sentiment_data.set_index("Sentiment"))

# ✅ Daily Affirmations
if st.session_state.user_id:
    st.subheader("🌞 Daily Affirmations")
    affirmations = [
        "You are strong, capable, and resilient.",
        "You are worthy of love and happiness.",
        "Every day, you grow and become a better version of yourself.",
        "You have the power to overcome challenges.",
        "Your feelings are valid, and you deserve peace."
    ]
    st.write(f"✨ {affirmations[torch.randint(0, len(affirmations), (1,)).item()]} ✨")