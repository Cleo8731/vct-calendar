from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config


def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if config.TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, config.SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(config.GOOGLE_CLIENT_CONFIG, config.SCOPES)
            creds = flow.run_local_server(port=0)
        with config.TOKEN_PATH.open("w") as token:
            token.write(creds.to_json())
    return creds


def get_calendar_service():
    return build("calendar", "v3", credentials=get_credentials())
