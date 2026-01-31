from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database import crud, models
from app.schemas.feedback import FeedbackResponse
from app.api.deps import get_current_user
from app.database.models import User, Email

router = APIRouter()

@router.post("/feedback")
async def feedback(
    email_id: str = Form(None),
    priority: str = Form(None),
    is_correct: str = Form(None),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save user feedback to ORM database"""
    try:
        data = await request.json()
        email_id = email_id or data.get("email_id") or data.get("id") or data.get("emailId")
        priority = priority or data.get("priority") or data.get("prioritySelected")
        is_correct = is_correct or data.get("is_correct") or data.get("correct")
    except:
        pass

    # Handle boolean conversion
    is_correct_bool = True if str(is_correct).lower() in ["true", "1", "yes"] else False

    if not email_id or not priority:
        return {"success": False, "error": "Missing required fields"}

    # Security check: Does this email belong to current_user?
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
         return {"success": False, "error": "Email not found or access denied"}

    crud.create_feedback(db, email_id, priority, is_correct_bool)

    return {"success": True, "message": "Feedback saved successfully"}

@router.get("/feedback")
def feedback_list(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all feedback records"""
    feedbacks = db.query(models.Feedback).order_by(models.Feedback.timestamp.desc()).all()
    return [
        {
            "email_id": f.email_id,
            "priority": f.priority,
            "is_correct": f.is_correct,
            "timestamp": f.timestamp
        }
        for f in feedbacks
    ]

@router.get("/feedback-stats")
def feedback_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get feedback statistics"""
    total = db.query(models.Feedback).count()
    correct = db.query(models.Feedback).filter(models.Feedback.is_correct == True).count()
    priorities = db.query(models.Feedback.priority).all()

    priority_count = {}
    for (p,) in priorities:
        priority_count[p] = priority_count.get(p, 0) + 1

    accuracy = round((correct / total * 100) if total > 0 else 0, 2)

    return {
        "total_feedback": total,
        "correct_classifications": correct,
        "accuracy": accuracy,
        "feedback_by_priority": priority_count
    }