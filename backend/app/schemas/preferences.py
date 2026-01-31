from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# User Preference Schemas
class UserPreferenceBase(BaseModel):
    primary_role: Optional[str] = None
    interests: Optional[List[str]] = None # Transformed to/from JSON/CSV in logic if needed
    about_user: Optional[str] = None

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreferenceResponse(UserPreferenceBase):
    id: int
    user_email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Sender Rule Schemas
class SenderRuleBase(BaseModel):
    sender_email: str
    force_priority: Optional[str] = None # 'High', 'Medium', 'Low'
    auto_reply: bool = False

class SenderRuleCreate(SenderRuleBase):
    pass

class SenderRuleResponse(SenderRuleBase):
    id: int
    user_email: str
    created_at: datetime

    class Config:
        from_attributes = True
