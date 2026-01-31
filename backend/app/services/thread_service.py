import os
from sqlalchemy.orm import Session
from app.database.models import Email
from app.utils.subject_similarity import subject_similarity

def assign_smart_thread_id(db: Session, user_email: str, subject: str) -> str:
    emails = db.query(Email).filter(Email.user_email == user_email).all()

    best_match = None
    best_score = 0

    for email in emails:
        # Assuming subject_similarity returns 0-100 or similar
        score = subject_similarity(subject, email.subject)
        if score > 85 and score > best_score:
            best_match = email.smart_thread_id
            best_score = score

    # If no match found → create new smart thread id
    if not best_match:
        return f"smart-{os.urandom(4).hex()}"

    return best_match