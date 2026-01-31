from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReplyRequest(BaseModel):
    email_id: str
    tone: str

class ReplyResponse(BaseModel):
    email_id: str
    generated_reply: Optional[str] = None # Deprecated/fallback
    reply_subject: Optional[str] = None
    reply_body: Optional[str] = None
    tone: str

class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

class SendReplyRequest(BaseModel):
    email_id: str
    reply_text: str

class AutoReplyRequest(BaseModel):
    email_id: str
    tone: str = "formal"

class DraftSaveRequest(BaseModel):
    email_id: str
    user_email: str
    draft_text: str
    tone: str

class DraftResponse(BaseModel):
    email_id: str = None
    draft_text: str
    tone: str
    updated_at: Optional[datetime]
    subject: Optional[str] = None # Added for list view

    class Config:
        from_attributes = True