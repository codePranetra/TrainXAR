import streamlit as st
from main import answer_question
import uuid
from chat_db import log_to_mysql
import re

st.set_page_config(page_title="TrainXar", page_icon="🤖")
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())  # Unique ID per session

if "history" not in st.session_state:
    st.session_state.history = []

def clear_chat():
    st.session_state.history = []

def format_bot_response(response):
    """Format bot response with proper line breaks and structure"""
    # Replace \n with actual line breaks for markdown
    formatted = response.replace('\\n', '\n')
    
    # Handle bullet points and lists
    formatted = re.sub(r'^\s*[-*]\s+', '- ', formatted, flags=re.MULTILINE)
    
    # Handle numbered lists
    formatted = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', formatted, flags=re.MULTILINE)
    
    # Handle bold text
    formatted = re.sub(r'\*\*(.*?)\*\*', r'**\1**', formatted)
    
    # Handle italic text
    formatted = re.sub(r'\*(.*?)\*', r'*\1*', formatted)
    
    return formatted

with st.sidebar:
    st.button("Clear chat", on_click=clear_chat)

st.header("TrainXar QA Bot")

query = st.text_input("Ask me anything about TrainXar:", placeholder="Type your question here...")
if query.strip():
    with st.spinner("Typing..."):
        try:
            answer, sources = answer_question(query, user_id=st.session_state.user_id)

        except Exception as e:
            st.error(f"Failed to get an answer: {e}")
        else:
            st.session_state.history.append({
                "query": query,
                "answer": answer,
                "sources": sources
            })

# Display chat history with proper formatting
for turn in st.session_state.history:
    # User message
    st.markdown(f"**You:** {turn['query']}")
    
    # Bot response with proper formatting
    formatted_answer = format_bot_response(turn['answer'])
    st.markdown(f"**Bot:** {formatted_answer}")
    
    # Add some spacing between messages
    st.markdown("---")
  
