import requests
import os 

from dotenv import load_dotenv

load_dotenv()
NOTIFICATION_TOPIC=os.getenv("NOTIFICATION_TOPIC")

def send_notification(summary: str, title: str = "High Alert Emails"):
    headers={
        "Title": title
    }



    if not NOTIFICATION_TOPIC:
        print("⚠️ Warning: NOTIFICATION_TOPIC is not set. Skipping notification.")
        return

    try:
        response = requests.post(
            f"https://ntfy.sh/{NOTIFICATION_TOPIC}",
            data=summary.encode("utf-8"),
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ Notification sent to ntfy.sh/{NOTIFICATION_TOPIC}")
        else:
            print(f"❌ Notification failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Notification Exception: {e}")