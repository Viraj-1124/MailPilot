from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from app.core.config import settings
import requests
import os
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.crud import get_user_by_email, create_user
from app.core.security import create_access_token
from app.core.crypto import encrypt_data
from datetime import timedelta
from app.api.deps import get_current_user
from app.database.models import User

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]


def get_google_client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }


@router.get("/login-url")
def login_url():
    """Generate Gmail OAuth URL"""
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return {"auth_url": auth_url}


@router.get("/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    """Google OAuth callback"""
    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    user_email = None
    try:
        if creds.id_token and "email" in creds.id_token:
            user_email = creds.id_token["email"]
        else:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {creds.token}"}
            )
            user_email = response.json().get("email", "unknown")
    except Exception as e:
        return {"error": f"Failed to fetch user info: {str(e)}"}

    if not creds.refresh_token:
        print("⚠️ Missing refresh_token. User must re-consent next login.")

    os.makedirs(settings.TOKENS_DIR, exist_ok=True)
    with open(f"{settings.TOKENS_DIR}/{user_email}.json", "w") as token_file:
        encrypted_json = encrypt_data(creds.to_json())
        token_file.write(encrypted_json)

    # Check if user exists, create if not
    user = get_user_by_email(db, email=user_email)
    if not user:
        user = create_user(db, email=user_email)
    
    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    print(f"✅ Logged in as: {user_email}")
    
    response = RedirectResponse(
        url="http://localhost:5173/dashboard",
        status_code=302
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set to True in production (HTTPS)
    )
    
    return response

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Get current logged in user"""
    return {"email": user.email}

@router.post("/logout")
def logout():
    """Logout user by clearing cookie"""
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    return response