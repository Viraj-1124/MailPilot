import os
import base64
import datetime
import ssl
import requests

from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from app.core.config import settings
from app.core.crypto import encrypt_data, decrypt_data
import json

# Ignore SSL verification warnings
ssl._create_default_https_context = ssl._create_unverified_context
requests.packages.urllib3.disable_warnings()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile"
]

def authenticate_gmail(user_email: str):
    """Authenticate Gmail for a specific user."""
    os.makedirs(settings.TOKENS_DIR, exist_ok=True)
    token_path = f"{settings.TOKENS_DIR}/{user_email}.json"

    creds = None
    if os.path.exists(token_path):
        try:
            with open(token_path, "r") as token:
                encrypted_data = token.read()
                # Decrypt data
                json_data = decrypt_data(encrypted_data)
                if not json_data:
                    raise ValueError("Decryption returned empty data")
                
                # Parse JSON and create credentials
                info = json.loads(json_data)
                creds = Credentials.from_authorized_user_info(info, SCOPES)
        except Exception:
            # If decryption fails or file is corrupt, delete it and force re-login
            print(f"⚠️ Token for {user_email} is invalid/corrupt. Deleting.")
            os.remove(token_path)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Re-save refreshed token (encrypted)
            with open(token_path, 'w') as token:
                token.write(encrypt_data(creds.to_json()))
        else:
            # For server-side rendering, we can't really run local server flow if user is not present.
            # But the original code had this fallback.
            flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save new token (encrypted)
            with open(token_path, 'w') as token:
                token.write(encrypt_data(creds.to_json()))

    return build('gmail', 'v1', credentials=creds)

def get_last_24h_emails(service):
    """Fetch emails received in last 24 hours."""
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    query = f"after:{int(yesterday.timestamp())}"
    results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
    return results.get('messages', [])

def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def get_email_details(service, msg_id):
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()

    headers = email_headers = msg["payload"]["headers"]
    parts = msg["payload"].get("parts", [])

    sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")

    full_text = ""
    attachments = []

    if not parts:
        # Handle cases where email has no parts (simple text/plain)
        body = msg["payload"].get("body", {})
        data = body.get("data")
        if data:
            decoded = decode_base64(data)
            full_text = decoded

    else:
        for part in parts:
            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")
            body = part.get("body", {})

            # Attachments
            if filename:
                attachments.append({
                    "filename": filename,
                    "mime_type": mime_type,
                    "size": body.get("size", 0),
                    "attachment_id": body.get("attachmentId")
                })
                continue

            data = body.get("data")
            if not data:
                # Multipart emails might have nested parts
                if part.get("parts"):
                     for subpart in part.get("parts"):
                        sub_mime = subpart.get("mimeType", "")
                        sub_body = subpart.get("body", {})
                        sub_data = sub_body.get("data")
                        if sub_data:
                            decoded = decode_base64(sub_data)
                            if sub_mime == "text/plain":
                                full_text += decoded
                            elif sub_mime == "text/html":
                                full_text += html_to_text(decoded)
                continue

            decoded = decode_base64(data)

            if mime_type == "text/plain":
                full_text += decoded
            elif mime_type == "text/html":
                full_text += html_to_text(decoded)

    full_text = " ".join(full_text.split())
    preview = full_text[:200] + "..." if len(full_text) > 200 else full_text

    thread_id = msg.get("threadId")
    internal_date = msg.get("internalDate")
    timestamp = datetime.datetime.fromtimestamp(int(internal_date) / 1000) if internal_date else datetime.datetime.now()

    is_read = "UNREAD" not in msg.get("labelIds", [])

    return sender, subject, preview, full_text, thread_id, attachments, timestamp, is_read

def send_email_via_gmail(user_email, to_email, subject, body):
    service = authenticate_gmail(user_email)

    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    send_body = {"raw": raw_message}

    sent_msg = service.users().messages().send(
        userId="me",
        body=send_body
    ).execute()

    return sent_msg