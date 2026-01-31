from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EmailTaskResponse(BaseModel):
    id: int
    task_text: str
    deadline: Optional[datetime] = None
    completed: bool
    source: str
    created_at: Optional[datetime] = None
    email_id: str

    class Config:
        from_attributes = True

class EmailTaskExtractionResponse(BaseModel):
    skipped: bool
    tasks: List[EmailTaskResponse]
    reason: Optional[str] = None
