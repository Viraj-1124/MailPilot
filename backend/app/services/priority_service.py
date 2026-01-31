import json
from typing import List, Optional
from app.database.models import UserPreference, SenderRule

def resolve_email_priority(
    sender: str,
    subject: str,
    body: str,
    ai_priority: str,
    user_pref: Optional[UserPreference],
    sender_rules: List[SenderRule]
) -> str:
    """
    Resolve the final priority of an email based on rules, preferences, and AI.
    
    Resolution Order:
    1. Sender Rule (Force Priority) -> FINAL
    2. Interest Match (Boost Priority)
    3. AI Priority (Fallback)
    """
    
    # 1. Check Sender Rules
    normalized_sender = sender.lower() if sender else ""
    for rule in sender_rules:
        if rule.sender_email.lower() in normalized_sender:
            if rule.force_priority:
                print(f"Priority Forced by Sender Rule ({rule.sender_email}): {rule.force_priority}")
                return rule.force_priority

    # 2. Check User Interests (Boost)
    # ai_priority is typically "High", "Medium", "Low"
    current_priority = ai_priority
    
    if user_pref and user_pref.interests:
        try:
            interests = json.loads(user_pref.interests)
        except:
            interests = []
            
        text_content = (subject + " " + body).lower()
        
        for interest in interests:
            if interest.lower() in text_content:
                # Boost Logic
                if current_priority == "Low":
                    print(f"Priority Boosted (Low -> Medium) due to interest: {interest}")
                    current_priority = "Medium"
                elif current_priority == "Medium":
                    print(f"Priority Boosted (Medium -> High) due to interest: {interest}")
                    current_priority = "High"
                elif current_priority == "High":
                    print(f"Priority Retained (High) due to interest: {interest}")
                
                # We apply one boost and exit (or cumulative? prompt implies "boost priority")
                # Let's stick to single boost for now to avoid over-alerting
                return current_priority

    # 3. Fallback to AI
    return current_priority


def get_auto_reply_rule(sender: str, sender_rules: List[SenderRule]) -> Optional[SenderRule]:
    """
    Check if a sender triggers an auto-reply.
    """
    normalized_sender = sender.lower() if sender else ""
    for rule in sender_rules:
        if rule.sender_email.lower() in normalized_sender and rule.auto_reply:
             return rule
    return None
