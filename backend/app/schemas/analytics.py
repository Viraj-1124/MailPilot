
from pydantic import BaseModel
from typing import Dict, Optional

class UserAnalytics(BaseModel):
    user_email: str
    total_emails: int
    total_attachments: int
    priority_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    thread_count: int
    average_summary_length: float
    activity_timeline: Dict[str, int]

class SystemAnalytics(BaseModel):
    total_users: int
    total_emails: int
    total_feedback: int
    model_accuracy: float
    most_common_category: Optional[str]
    most_common_priority: Optional[str]
    priority_distribution: Dict[str, int]
    category_distribution: Dict[str, int]