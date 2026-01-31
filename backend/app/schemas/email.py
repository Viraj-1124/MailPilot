
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AttachmentSchema(BaseModel):
    filename: str
    mime_type: str
    size: int
    attachment_id: str

    class Config:
        from_attributes = True

class EmailBase(BaseModel):
    email_id: str
    from_: str
    subject: str
    summary: Optional[str] = None
    priority: Optional[str] = "Medium"
    timestamp: Optional[datetime] = None

class EmailDetail(BaseModel):
    email_id: str
    from_: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    timestamp: Optional[datetime] = None
    attachments: Optional[List[AttachmentSchema]] = []
    is_archived: Optional[bool] = False
    is_deleted: Optional[bool] = False

class EmailListResponse(BaseModel):
    overall_summary: Optional[str] = None
    emails: List[EmailBase]

class SmartThreadItem(BaseModel):
    email_id: str
    subject: str
    summary: Optional[str]
    priority: Optional[str]
    category: Optional[str]
    timestamp: Optional[datetime]

class SmartThread(BaseModel):
    smart_thread_id: str
    emails: List[SmartThreadItem]

class ThreadGroup(BaseModel):
    group_key: str
    emails: List[SmartThreadItem]