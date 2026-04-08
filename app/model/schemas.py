from pydantic import BaseModel #why

class Message(BaseModel):
    text: str