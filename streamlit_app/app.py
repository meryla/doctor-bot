import streamlit as st  # Streamlit = frontend UI framework
import requests         # requests = send HTTP requests to  FastAPI backend

# Configure the page (title + icon in browser tab)
st.set_page_config(page_title="AI Assistant", page_icon="🤖")

# App title
st.title("🤖 AI Assistant")


# ---------------------------------------------------
# INIT MEMORY (ONLY RUNS ONCE)
# ---------------------------------------------------
# This initializes conversation memory using Streamlit session state.
# Think of it as storing chat history for this user session.
#
# The "system" message is like instructions for the AI (its behavior/rules).
#
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """
You are an AI assistant with access to tools.

Rules:
- Use tools when needed
- You can call multiple tools
- Do not guess when tools are available
"""
        }
    ]


# ---------------------------------------------------
# DISPLAY CHAT HISTORY
# ---------------------------------------------------
# This loops through all stored messages and displays them in the UI.
#
# st.chat_message(role) creates a chat bubble (user or assistant).
# st.write(content) prints the message inside the bubble.
#
for msg in st.session_state.messages:
    if msg["role"] != "system":  # don't show system message to user
        with st.chat_message(msg["role"]):
            st.write(msg["content"])


# ---------------------------------------------------
# USER INPUT
# ---------------------------------------------------
# chat_input creates a chat box (like ChatGPT input)
user_input = st.chat_input("Ask something...")

# If user typed something
if user_input:

    # Save user message in memory
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_input)

    # ---------------------------------------------------
    # SEND FULL MEMORY TO BACKEND
    # ---------------------------------------------------
    # requests.post(...) sends an HTTP request to your FastAPI server.
    #
    # "http://localhost:8000/chat"
    # → This is your endpoint (running locally).
    #
    # json={...}
    # → This sends data as JSON to the backend.
    #
    # IMPORTANT:
    # We send the FULL conversation (not just the last message)
    # so the AI has memory/context.
    #
    response = requests.post(
        "http://localhost:8000/chat",
        json={"messages": st.session_state.messages}
    )

    # ---------------------------------------------------
    # HANDLE BACKEND RESPONSE
    # ---------------------------------------------------
    # response.status_code == 200 means:
    # Request succeeded (HTTP OK)
    #
    if response.status_code == 200:

        # response.json() converts backend response into Python dict
        reply = response.json()["reply"]

        # Save assistant response in memory
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })

        # Display assistant response
        with st.chat_message("assistant"):
            st.write(reply)

    else:
        # If backend fails (server down, error, etc.)
        st.error("Error connecting to API")