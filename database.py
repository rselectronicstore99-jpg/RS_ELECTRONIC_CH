import os
import json
import random
import string
import gspread
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
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

# database.py లోని పాత ఆథెంటికేషన్ కోడ్ తీసేసి ఈ క్రింది విధంగా మార్చండి

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_service_account_creds():
    """Streamlit Secrets నుండి కీని సురక్షితంగా రీడ్ చేస్తుంది"""
    if "google_credentials" not in st.secrets:
        st.error("Error: Streamlit Secrets లో 'google_credentials' కాన్ఫిగర్ చేయలేదు!")
        return None
    try:
        creds_dict = json.loads(st.secrets["google_credentials"])
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception as e:
        st.error(f"❌ కీ రీడింగ్ లోపం: {e}")
        return None

def get_google_credentials():
    """గూగుల్ డ్రైవ్ అప్‌లోడ్ కోసం సర్వీస్ అకౌంట్ కీ ని వాడుతుంది"""
    return get_service_account_creds()

def get_gspread_sheet():
    """గూగుల్ షీట్ యాక్సెస్ కోసం"""
    creds = get_service_account_creds()
    if not creds:
        return None
    client = gspread.authorize(creds)
    
    # ⚠️ గమనిక: ఇక్కడ మీ అసలు గూగుల్ షీట్ పేరును కరెక్ట్‌గా రాయండి!
    sheet = client.open("RS_Customers").sheet1 
    return sheet

def generate_random_key(prefix="RS", length=4):
    numbers = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}-{numbers}"