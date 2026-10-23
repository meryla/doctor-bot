from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import User, CalendarCredential
from app.services.ai import run_agent  # votre logique d'agent

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cet endpoint reçoit toute la conversation depuis Streamlit,
    récupère les identifiants Google Calendar de l'utilisateur connecté,
    exécute l'agent IA et renvoie la réponse de l'assistant.
    """

    # ---------------------------------------------------
    # RECEVOIR LES MESSAGES DU FRONTEND
    # ---------------------------------------------------
    messages = data["messages"]

    # ---------------------------------------------------
    # RÉCUPÉRER LES CREDENTIALS DU CALENDRIER DE L'UTILISATEUR
    # ---------------------------------------------------
    creds_record = await db.get(CalendarCredential, current_user.id)

    # ---------------------------------------------------
    # LNCER L'AGENT (AVEC LES CREDENTIALS)
    # ---------------------------------------------------
    reply = run_agent(messages=messages, creds_record=creds_record)

    # ---------------------------------------------------
    # RENVOYER LA RÉPONSE AU FRONTEND
    # ---------------------------------------------------
    return {"reply": reply}