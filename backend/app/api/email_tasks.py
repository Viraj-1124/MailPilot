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


@router.patch("/tasks/{task_id}/complete", response_model=EmailTaskResponse)
def toggle_task_completion(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle the completion status of a task.
    """
    task = db.query(EmailTask).filter(EmailTask.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
        
    try:
        task.completed = not task.completed
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Task update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.post("/tasks/{task_id}/add-to-calendar")
def add_task_to_calendar(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a task to Google Calendar.
    """
    from app.services.gmail_service import get_calendar_service
    from datetime import timedelta

    # 1. Fetch Task & Verify Ownership
    task = db.query(EmailTask).filter(EmailTask.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")

    if task.calendar_event_id:
        return {"success": False, "message": "Task already added to calendar", "calendar_event_link": None}

    # 2. Authenticate Calendar Service
    try:
        service = get_calendar_service(current_user.email)
        if not service:
             raise HTTPException(status_code=401, detail="Google authentication failed. Please re-login.")
    except Exception as e:
        print(f"Calendar auth error: {e}")
        raise HTTPException(status_code=401, detail="Google authentication failed")

    # 3. Calculate Start/End
    if task.deadline:
        start_time = task.deadline
        description_suffix = ""
    else:
        # Default to 1 hour from now if no deadline
        start_time = datetime.now() + timedelta(hours=1)
        description_suffix = "\n(No deadline specified in email, scheduled for +1h)"

    end_time = start_time + timedelta(hours=1)

    # 4. Create Event Body
    event_body = {
        'summary': task.task_text,
        'description': f"Created by mAiL from email task.{description_suffix}\nSource: {task.source}",
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC', # Adjust if we had user timezone
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }

    # 5. Insert Event
    try:
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        
        # 6. Update Task
        task.calendar_event_id = event.get('id')
        db.commit()
        db.refresh(task)

        return {
            "success": True,
            "calendar_event_link": event.get('htmlLink')
        }

    except Exception as e:
        db.rollback()
        print(f"Calendar API Error: {e}")
        
        # Check if it's a permissions error
        # Google API errors are often JSON strings inside the exception message or HttpError objects
        error_str = str(e)
        if "insufficientPermissions" in error_str or "Insufficient Permission" in error_str:
             raise HTTPException(
                 status_code=403, 
                 detail="Insufficient permissions. Please Log Out and Log In again to grant Calendar access."
             )
             
        raise HTTPException(status_code=500, detail=f"Failed to add to calendar: {str(e)}")
