from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database import models
from app.schemas.analytics import UserAnalytics, SystemAnalytics
from app.api.deps import get_current_user
from app.database.models import User

router = APIRouter()

@router.get("/analytics/user")
def user_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_email = current_user.email

    total_emails = db.query(models.Email).filter(models.Email.user_email == user_email).count()

    total_attachments = (
        db.query(models.EmailAttachment)
        .join(models.Email, models.Email.email_id == models.EmailAttachment.email_id)
        .filter(models.Email.user_email == user_email)
        .count()
    )

    # Priority Distribution
    priorities = db.query(models.Email.priority).filter(models.Email.user_email == user_email).all()
    priority_count = {}
    for (p,) in priorities:
        priority_count[p] = priority_count.get(p, 0) + 1

    # Category Distribution
    categories = db.query(models.Email.category).filter(models.Email.user_email == user_email).all()
    category_count = {}
    for (c,) in categories:
        category_count[c] = category_count.get(c, 0) + 1

    # Total threads
    thread_count = (
        db.query(models.Email.thread_id)
        .filter(models.Email.user_email == user_email)
        .distinct()
        .count()
    )

    # Average summary length
    summaries = db.query(models.Email.summary).filter(models.Email.user_email == user_email).all()
    if summaries:
        # Filter out None summaries
        valid_summaries = [s[0] for s in summaries if s[0]]
        if valid_summaries:
            avg_summary_len = round(sum(len(s) for s in valid_summaries) / len(valid_summaries), 2)
        else:
             avg_summary_len = 0
    else:
        avg_summary_len = 0

    # Activity timeline (emails/day)
    activity = (
        db.query(models.Email.timestamp)
        .filter(models.Email.user_email == user_email)
        .all()
    )

    timeline = {}
    for (ts,) in activity:
        if ts:
            date_str = ts.date().isoformat()
            timeline[date_str] = timeline.get(date_str, 0) + 1

    return {
        "user_email": user_email,
        "total_emails": total_emails,
        "total_attachments": total_attachments,
        "priority_distribution": priority_count,
        "category_distribution": category_count,
        "thread_count": thread_count,
        "average_summary_length": avg_summary_len,
        "activity_timeline": timeline
    }


@router.get("/analytics/system")
def system_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    total_users = db.query(models.Email.user_email).distinct().count()
    total_emails = db.query(models.Email).count()
    total_feedback = db.query(models.Feedback).count()

    # Model accuracy from feedback table
    correct = db.query(models.Feedback).filter(models.Feedback.is_correct == True).count()
    accuracy = round((correct / total_feedback * 100), 2) if total_feedback > 0 else 0

    # Most common category
    categories = db.query(models.Email.category).all()
    category_count = {}
    for (c,) in categories:
        category_count[c] = category_count.get(c, 0) + 1

    most_common_category = max(category_count, key=category_count.get) if category_count else None

    # Most common priority
    priorities = db.query(models.Email.priority).all()
    priority_count = {}
    for (p,) in priorities:
        priority_count[p] = priority_count.get(p, 0) + 1

    most_common_priority = max(priority_count, key=priority_count.get) if priority_count else None

    return {
        "total_users": total_users,
        "total_emails": total_emails,
        "total_feedback": total_feedback,
        "model_accuracy": accuracy,
        "most_common_category": most_common_category,
        "most_common_priority": most_common_priority,
        "priority_distribution": priority_count,
        "category_distribution": category_count
    }