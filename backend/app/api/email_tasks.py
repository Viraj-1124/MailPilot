from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.database import get_db
from app.database.models import EmailTask, Email, User
from app.schemas.task import EmailTaskResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/tasks", response_model=List[EmailTaskResponse])
def get_user_tasks(
    user_email: str = Query(..., description="User's email address"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch all tasks for the current user.
    """
    if user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access these tasks")

    query = db.query(EmailTask).filter(EmailTask.user_email == current_user.email)

    if completed is not None:
        query = query.filter(EmailTask.completed == completed)

    tasks = query.order_by(EmailTask.created_at.desc()).all()
    return tasks


@router.get("/emails/{email_id}/tasks", response_model=List[EmailTaskResponse])
def get_email_tasks(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch tasks linked to a specific email.
    Verifies that the email exists and belongs to the user.
    """
    # Verify email ownership
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        pass

    # Re-evaluating requirement: "If mismatch -> 403 Forbidden"
    # To implement exactly:
    check_email = db.query(Email).filter(Email.email_id == email_id).first()
    if not check_email:
         raise HTTPException(status_code=404, detail="Email not found")
    
    if check_email.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this email")

    # If we are here, it's safe.
    tasks = db.query(EmailTask).filter(
        EmailTask.email_id == email_id,
        EmailTask.user_email == current_user.email
    ).order_by(EmailTask.created_at.desc()).all()

    return tasks
