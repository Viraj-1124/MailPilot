from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.sheduler import start_scheduler
from app.database.database import Base, engine
from app.api import auth, emails, replies, feedback, analytics, categories, email_tasks
from dotenv import load_dotenv
load_dotenv()


# Create tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Start API Scheduler
start_scheduler()

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import Email
from datetime import datetime, timedelta

@app.on_event("startup")
def cleanup_emails():
    """Cleanup old emails on startup"""
    try:
        db: Session = SessionLocal()
        now = datetime.now()
        
        # Trash: 30 days
        trash_limit = now - timedelta(days=30)
        db.query(Email).filter(Email.is_deleted == True, Email.deleted_at < trash_limit).delete()
        
        # Archive: 90 days
        archive_limit = now - timedelta(days=90)
        db.query(Email).filter(Email.is_archived == True, Email.archived_at < archive_limit).delete()
        
        db.commit()
        db.close()
        print("Cleanup completed.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

    try:
        # DB Migration for is_read column (Hackathon safe)
        db: Session = SessionLocal()
        from sqlalchemy import text
        try:
            db.execute(text("ALTER TABLE emails ADD COLUMN is_read BOOLEAN DEFAULT 0"))
            db.commit()
            print("Migration: Added is_read column.")
        except Exception as e:
            # Column likely exists
            # print(f"Migration skipped (likely exists): {e}")
            pass
        db.close()
    except Exception:
        pass

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(emails.router, tags=["Emails"])
app.include_router(replies.router, tags=["Replies"])
app.include_router(feedback.router, tags=["Feedback"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(categories.router, tags=["Categories"])
app.include_router(email_tasks.router, tags=["Tasks"])

@app.get("/")
def root():
    return {"message": "mAiL API is running 🚀 (Refactored)"}

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "mAiL backend running"
    }