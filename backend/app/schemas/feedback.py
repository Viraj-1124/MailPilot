from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    email_id: str
    priority: str
    is_correct: bool

class FeedbackResponse(FeedbackCreate):
    timestamp: Optional[datetime]

    class Config:
        from_attributes = True

class FeedbackStats(BaseModel):
    total_feedback: int
    correct_classifications: int
    accuracy: float
    feedback_by_priority: dict