# Calm Sphere - Mental Health Chatbot  

Calm Sphere is an AI-powered mental health chatbot designed to offer emotional support and promote well-being. Built using Streamlit, MongoDB, Hugging Face, and LLaMA 3, it engages users in meaningful conversations, provides mood analysis, and offers insights to help manage mental health effectively.  

## Features  

Calm Sphere offers:  

- An AI chatbot for supportive conversations.  
- Emotion detection through natural language processing.  
- Secure user management with personalized interactions.  
- Mood analysis, sentiment distribution, and word cloud visualizations.  
- Daily affirmations for positivity.  
- An incognito mode for private conversations.  

## Technology Stack  

This project uses:  

- Streamlit for the user interface.  
- Python for backend development.  
- MongoDB for data storage.  
- Hugging Face LLaMA 3 for AI-powered conversations.  
- Matplotlib and WordCloud for data visualization.  

## Installation Guide  

Follow these steps to install and run Calm Sphere:  

1. Clone the repository using `git clone`.  
2. Navigate to the project directory.  
3. Create a virtual environment using `python -m venv env` and activate it.  
4. Install dependencies with `pip install -r requirements.txt`.
5. Create a `.env` file and provide the Hugging Face API key and MongoDB connection URI.  
6. Run the application using `streamlit run ui.py --server.enableCORS false --server.enableXsrfProtection false`.  

## Usage Instructions  

- Log in using your username or register as a new user.  
- Start a conversation with Calm Sphere for support.  
- View mood analysis and sentiment insights from your chat history.  
- Receive daily affirmations for motivation.  
- Enable incognito mode for privacy when needed.  
