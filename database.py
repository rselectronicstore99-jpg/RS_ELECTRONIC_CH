import os
import json
import random
import string
import gspread
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

# --- కాన్ఫిగరేషన్ మరియు పాత్‌లు ---
FOLDER_ID = "1edC-hDNWiBqgeLd_NQeixkYR07OOc5Dp" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "shop_config.json")
AUTOSUGGEST_FILE = os.path.join(BASE_DIR, "autosuggest_database.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SESSION_FILE = os.path.join(BASE_DIR, "local_user_session.json") 
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
SIGN_PATH = os.path.join(BASE_DIR, "sign.png")

def get_financial_year():
    now = datetime.now()
    return f"{now.year}_{now.year + 1}" if now.month >= 4 else f"{now.year - 1}_{now.year}"

HISTORY_FILE = os.path.join(BASE_DIR, f"challana_history_{get_financial_year()}.json")

def load_json(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r") as f: return json.load(f)
    return default_val

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)

def get_google_credentials():
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = None
    if os.path.exists(TOKEN_FILE):
        try: creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except: pass
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(Request())
            except: creds = None
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                st.error("Error: 'credentials.json' ఫైల్ లభించలేదు!")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(TOKEN_FILE, 'w') as token: token.write(creds.to_json())
            except Exception as e:
                st.error(f"❌ గూగుల్ అథెంటికేషన్ లోపం: {e}")
                return None
    return creds

def upload_to_drive(file_path):
    try:
        creds = get_google_credentials()
        if not creds: return None
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(file_path), 'parents': [FOLDER_ID]}
        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return uploaded_file.get('id')
    except Exception as e:
        st.error(f"గూగుల్ డ్రైవ్ అప్‌లోడ్ ఎర్రర్: {e}")
        return None

def get_gspread_sheet():
    creds = get_google_credentials()
    if not creds: raise Exception("గూగుల్ అథెంటికేషన్ కనెక్ట్ కాలేదు!")
    client = gspread.authorize(creds)
    return client.open("RS_Customers").sheet1

def generate_random_key(prefix="RS", length=4):
    numbers = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}-{numbers}"