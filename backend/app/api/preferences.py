from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
from app.database.database import get_db
from app.database.models import UserPreference, SenderRule, User
from app.schemas.preferences import (
    UserPreferenceCreate, UserPreferenceResponse,
    SenderRuleCreate, SenderRuleResponse
)
from app.api.deps import get_current_user

router = APIRouter()

# --------------------------
# User Preferences Endpoints
# --------------------------

@router.post("/preferences", response_model=UserPreferenceResponse)
def create_or_update_preferences(
    pref_data: UserPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update user preferences (Role, Interests, About).
    """
    pref = db.query(UserPreference).filter(UserPreference.user_email == current_user.email).first()

    # Convert list to JSON string for storage
    interests_str = json.dumps(pref_data.interests) if pref_data.interests else "[]"

    if pref:
        pref.primary_role = pref_data.primary_role
        pref.interests = interests_str
        pref.about_user = pref_data.about_user
    else:
        pref = UserPreference(
            user_email=current_user.email,
            primary_role=pref_data.primary_role,
            interests=interests_str,
            about_user=pref_data.about_user
        )
        db.add(pref)

    db.commit()
    db.refresh(pref)

    # Convert back to list for response
    # We can use a property or helper, but Pydantic expects a dict/object to validate
    # We manually patch the object for Pydantic serialization since 'interests' is a string in DB
    pref_response = UserPreferenceResponse(
        id=pref.id,
        user_email=pref.user_email,
        primary_role=pref.primary_role,
        interests=json.loads(pref.interests) if pref.interests else [],
        about_user=pref.about_user,
        created_at=pref.created_at
    )
    return pref_response


@router.get("/preferences", response_model=UserPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user preferences.
    """
    pref = db.query(UserPreference).filter(UserPreference.user_email == current_user.email).first()
    
    if not pref:
        # Return empty default structure if none exist
        return UserPreferenceResponse(
            id=0, # Dummy ID
            user_email=current_user.email,
            primary_role=None,
            interests=[],
            about_user=None,
            created_at=None 
        )

    return UserPreferenceResponse(
        id=pref.id,
        user_email=pref.user_email,
        primary_role=pref.primary_role,
        interests=json.loads(pref.interests) if pref.interests else [],
        about_user=pref.about_user,
        created_at=pref.created_at
    )


# --------------------------
# Sender Rules Endpoints
# --------------------------

@router.post("/sender-rules", response_model=SenderRuleResponse)
def create_or_update_sender_rule(
    rule_data: SenderRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update a rule for a specific sender.
    """
    existing_rule = db.query(SenderRule).filter(
        SenderRule.user_email == current_user.email,
        SenderRule.sender_email == rule_data.sender_email
    ).first()

    if existing_rule:
        existing_rule.force_priority = rule_data.force_priority
        existing_rule.auto_reply = rule_data.auto_reply
        db.commit()
        db.refresh(existing_rule)
        return existing_rule
    else:
        new_rule = SenderRule(
            user_email=current_user.email,
            sender_email=rule_data.sender_email,
            force_priority=rule_data.force_priority,
            auto_reply=rule_data.auto_reply
        )
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        return new_rule


@router.get("/sender-rules", response_model=List[SenderRuleResponse])
def get_sender_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all sender rules for the current user.
    """
    rules = db.query(SenderRule).filter(SenderRule.user_email == current_user.email).all()
    return rules
