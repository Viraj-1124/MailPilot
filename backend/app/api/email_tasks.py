from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database.database import get_db
from app.database.models import EmailTask, Email, User
from app.schemas.task import EmailTaskResponse, EmailTaskExtractionResponse
from app.api.deps import get_current_user
from app.services.task_extractor import should_extract_tasks, extract_tasks_from_email
from dateutil import parser  
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
    
    # Re-evaluating requirement: "If mismatch -> 403 Forbidden"
    check_email = db.query(Email).filter(Email.email_id == email_id).first()
    if not check_email:
         raise HTTPException(status_code=404, detail="Email not found")
    
    if check_email.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this email")

    tasks = db.query(EmailTask).filter(
        EmailTask.email_id == email_id,
        EmailTask.user_email == current_user.email
    ).order_by(EmailTask.created_at.desc()).all()

    return tasks


@router.post("/emails/{email_id}/extract-tasks", response_model=EmailTaskExtractionResponse)
def extract_tasks_on_demand(
    email_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    On-demand AI task extraction.
    Checks pre-filter and existing tasks before calling AI.
    """
    
    # 1. Fetch Email & Verify Ownership
    email = db.query(Email).filter(Email.email_id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this email")
        
    # 2. Check for existing tasks
    existing_tasks = db.query(EmailTask).filter(
        EmailTask.email_id == email_id,
        EmailTask.user_email == current_user.email
    ).all()
    
    if existing_tasks:
        return {
            "skipped": True,
            "reason": "Tasks already exist",
            "tasks": existing_tasks
        }
    
    # 3. Run heuristic pre-filter
    should_run = should_extract_tasks(
        subject=email.subject or "",
        body=email.body or "",
        category=email.category,
        priority=email.priority
    )
    
    if not should_run:
        return {
            "skipped": True,
            "reason": "low_signal_email",
            "tasks": []
        }
        
    # 4. Run AI Extraction
    # Note: AI extraction returns natural language deadline string. 
    # We need to be careful saving to DateTime column.
    
    extraction_result = extract_tasks_from_email(email.subject, email.body)
    
    if not extraction_result.get("has_tasks", False):
         return {
            "skipped": False, # AI ran but found nothing
            "tasks": []
        }
        
    extracted_tasks_data = extraction_result.get("tasks", [])
    new_task_objects = []
    
    try:
        for task_data in extracted_tasks_data:
            # Deadline Parsing Logic
            deadline_dt = None
            raw_deadline = task_data.get("deadline")
            if raw_deadline:
                try:
                    deadline_dt = parser.parse(raw_deadline, fuzzy=True)
                except:
                    deadline_dt = None # Keep as None if unparseable
            
            new_task = EmailTask(
                email_id=email_id,
                user_email=current_user.email,
                task_text=task_data["task_text"],
                deadline=deadline_dt,
                source="ai",
                completed=False,
                created_at=datetime.now()
            )
            db.add(new_task)
            new_task_objects.append(new_task)
            
        db.commit()
        
        # Refresh to get IDs
        for t in new_task_objects:
            db.refresh(t)
            
        return {
            "skipped": False,
            "tasks": new_task_objects
        }
        
    except Exception as e:
        db.rollback()
        print(f"Task persistence failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save tasks")
