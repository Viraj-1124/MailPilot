from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Email, User
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/category-stats")
def category_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emails = db.query(Email).filter(Email.user_email == current_user.email).all()

    stats = {}
    for mail in emails:
        cat = mail.category
        stats[cat] = stats.get(cat, 0) + 1

    return stats