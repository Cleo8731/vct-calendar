import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

TOKEN_PATH = DATA_DIR / "token.json"
LAST_UPDATED_PATH = DATA_DIR / "last_updated.json"
WEB_CAL_PUBLIC_PATH = DATA_DIR / "web_cal_public.json"

SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_CLIENT_CONFIG = {
    "installed": {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }
}

VLR_URL = "https://www.vlr.gg"
REGION_ID = {
    "International": "all",
    "Americas": "26",
    "EMEA": "27",
    "Pacific": "28",
    "China": "24",
}

### Toggleables: ###
INCLUDE_EWC = False
INCLUDE_CHALLENGERS = False
INCLUDE_STRIKE_ARABIA = False
# Default match length in hours, by series type
SERIES_LEN_DEFAULT = 2
SERIES_LEN = {
    "Grand Final": 5,
    "Lower Final": 4.5,
    "Showmatch": 1,
}

LOG_TO_FILE = True
LOG_PATH = BASE_DIR / "log.txt"


def configure_logging():
    handlers = [logging.StreamHandler()]
    if LOG_TO_FILE:
        handlers.append(logging.FileHandler(LOG_PATH))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=handlers,
    )
