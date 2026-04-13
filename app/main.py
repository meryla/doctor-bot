from fastapi import FastAPI
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from app.services.ai import run_agent 
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API is working"}

@app.post("/chat")
def chat(data: dict):
    messages = data.get("messages", [])

    if not messages:
        return {"reply": "No messages received."}

    reply = run_agent(messages)
    return {"reply": reply}