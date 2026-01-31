import requests
import os 

from dotenv import load_dotenv

load_dotenv()
NOTIFICATION_TOPIC=os.getenv("NOTIFICATION_TOPIC")

def send_notification(summary: str):
    headers={
        "Title":"High Alert Emails"
    }



    requests.post(
        f"https://ntfy.sh/{NOTIFICATION_TOPIC}",
        data=summary.encode("utf-8"),
        headers=headers
    )