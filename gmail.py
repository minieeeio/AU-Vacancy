import base64
import os
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")          # needs GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = str(BASE_DIR / "token.json")

ACCOUNT_EMAIL = "lanuja667@gmail.com"  # <- the Gmail account to sign in with (sends the email)
TO = "batsanuja@gmail.com"             # <- change this to the address that should receive the email
SUBJECT = "Initials"
BODY = "Hello"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        client_config = {
            "installed": {
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0, login_hint=ACCOUNT_EMAIL)  # opens the browser the first time only

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
    return creds


def send_email(to, subject, body):
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service = build("gmail", "v1", credentials=get_credentials())
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


if __name__ == "__main__":
    send_email(TO, SUBJECT, BODY)
    print("Email sent.")