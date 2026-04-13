import streamlit as st
import requests
from todo_tab import render_todo_tab

st.set_page_config(
    page_title="DOC Assistant",
    page_icon="🤖👩🏻‍⚕️",
    layout="wide"
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
/* Main app background */
.stApp {
    background: linear-gradient(135deg, #fdf2f8, #fce7f3, #ede9fe);
    color: #2d1b3d;
}

/* Main container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}

/* Title styling */
.main-title {
    text-align: center;
    font-size: 3rem;
    font-weight: 800;
    color: #7c3aed;
    margin-bottom: 0.3rem;
}

.sub-title {
    text-align: center;
    font-size: 1.1rem;
    color: #6b7280;
    margin-bottom: 2rem;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(255, 255, 255, 0.35);
    padding: 10px;
    border-radius: 16px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    border-radius: 12px;
    padding: 10px 22px;
    background-color: white;
    color: #6d28d9;
    font-weight: 600;
    border: 1px solid #e9d5ff;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #c084fc, #f472b6);
    color: white !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

/* Chat message style */
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.78);
    border-radius: 18px;
    padding: 12px 16px;
    margin-bottom: 10px;
    border: 1px solid #f3e8ff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}

/* Chat input */
[data-testid="stChatInput"] {
    border-radius: 16px;
}

/* General input boxes */
.stTextInput > div > div > input,
.stTextArea textarea {
    border-radius: 12px !important;
    border: 1px solid #d8b4fe !important;
    background-color: #ffffff !important;
    color: #2d1b3d !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #a855f7, #ec4899);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
}

.stButton > button:hover {
    opacity: 0.92;
}

/* Error box */
.stAlert {
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown('<div class="main-title">🤖👩🏻‍⚕️ DOC Assistant 💅🏼</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your cute and helpful medical assistant workspace</div>', unsafe_allow_html=True)

assistant_tab, todo_tab = st.tabs(["🤖 Assistant", "✅ Daily To-Do"])

with assistant_tab:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.write(user_input)

        try:
            response = requests.post(
                "http://localhost:8000/chat",
                json={"messages": st.session_state.messages},
                timeout=60
            )

            if response.status_code == 200:
                reply = response.json()["reply"]

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply
                })

                with st.chat_message("assistant"):
                    st.write(reply)
            else:
                st.error(f"Error from API: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to API: {e}")

with todo_tab:
    render_todo_tab()