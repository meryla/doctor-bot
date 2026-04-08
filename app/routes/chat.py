from fastapi import APIRouter  # FastAPI router to define endpoints
from app.services.ai import run_agent  # your agent logic

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(data: dict):
    """
    This endpoint receives the FULL conversation from Streamlit,
    runs the AI agent, and returns the assistant's reply.
    """

    # ---------------------------------------------------
    # RECEIVE MESSAGES FROM FRONTEND
    # ---------------------------------------------------
    # data is the JSON sent by Streamlit:
    # { "messages": [...] }
    #
    # We extract the full conversation history here.
    #
    messages = data["messages"]

    # ---------------------------------------------------
    # IMPORTANT NOTE
    # ---------------------------------------------------
    # We DO NOT recreate messages here anymore.
    # The system message + history already comes from Streamlit.
    #
    # This keeps memory across the conversation.
    #

    # ---------------------------------------------------
    # RUN AGENT (TOOLS + MULTI-STEP REASONING)
    # ---------------------------------------------------
    reply = run_agent(messages)

    # ---------------------------------------------------
    # RETURN RESPONSE TO FRONTEND
    # ---------------------------------------------------
    # FastAPI automatically converts this dict → JSON
    #
    return {"reply": reply}