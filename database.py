import os
import json
import random
import string
import gspread
import uuid
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

# --- కాన్ఫిగరేషన్ మరియు పాత్‌లు ---
FOLDER_ID = "1edC-hDNWiBqgeLd_NQeixkYR07OOc5Dp" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
SIGN_PATH = os.path.join(BASE_DIR, "sign.png")
HISTORY_FILE = os.path.join(BASE_DIR, f"challana_history_{datetime.now().year}.json")

# --- 🔐 లైసెన్స్ సెక్యూరిటీ కీ (రెండు ఫైల్స్ లోనూ ఒకేలా ఉండాలి) ---
SECRET_SALT = "RS_ELECTRONIC_SUPER_SECRET_2026"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_safe_creds_dict():
    """Secrets లో టెక్స్ట్ లేదా డిక్షనరీ ఏదున్నా సేఫ్ గా రీడ్ చేస్తుంది"""
    if "google_credentials" not in st.secrets:
        st.error("Error: Streamlit Secrets లో 'google_credentials' కాన్ఫిగర్ చేయలేదు!")
        return None
    try:
        raw_creds = st.secrets["google_credentials"]
        if isinstance(raw_creds, str):
            return json.loads(raw_creds)
        else:
            return dict(raw_creds)
    except Exception as e:
        st.error(f"❌ కీ రీడింగ్ లోపం: {e}")
        return None

def get_service_account_creds():
    creds_dict = get_safe_creds_dict()
    if not creds_dict: return None
    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

def get_google_credentials():
    return get_service_account_creds()

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
    creds_dict = get_safe_creds_dict()
    if not creds_dict: return None
    gc = gspread.service_account_from_dict(creds_dict)
    sheet = gc.open("RS_Customers").sheet1 
    return sheet

def load_json(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r") as f: return json.load(f)
    return default_val

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)

# --- 🆕 సిస్టమ్ లైసెన్స్ ఫంక్షన్లు ---

def generate_system_id():
    """కొత్త కస్టమర్ కోసం సురక్షితమైన సిస్టమ్ నంబర్ క్రియేట్ చేస్తుంది"""
    return f"RS-{uuid.uuid4().hex[:5].upper()}-SYS"

def calculate_valid_key(system_id):
    """సిస్టమ్ నంబర్ మరియు సాల్ట్ ఆధారంగా కరెక్ట్ కీ ని లెక్కిస్తుంది"""
    import hashlib
    raw_string = f"{system_id}_{SECRET_SALT}"
    secure_hash = hashlib.sha256(raw_string.encode()).hexdigest().upper()
    return secure_hash[:8] # 8 అక్షరాల కీ

def register_system_customer(system_id, password, phone, shop_name, lic_1, lic_2, addr_1, addr_2):
    """అడ్మిన్ గూగుల్ షీట్ లో 12 కాలమ్స్ డేటాను కరెక్ట్ ఆర్డర్ లో అప్‌లోడ్ చేస్తుంది"""
    try:
        sheet = get_gspread_sheet()
        if not sheet: return False
        
        expiry_date_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        # app.py చదవగలిగే 12 కాలమ్స్ అమరిక
        new_row = [
            system_id,        # Col 1: Username
            password,         # Col 2: Password
            phone,            # Col 3: Phone_No
            "ACTIVE",         # Col 4: Status
            "Trial",          # Col 5: Key_Type
            expiry_date_str,  # Col 6: Expiry_Date
            "TRUE",           # Col 7: Profile_Setup_Done
            shop_name,        # Col 8: Shop_Name
            lic_1,            # Col 9: Lic_1
            lic_2,            # Col 10: Lic_2
            addr_1,           # Col 11: Address_Line1
            addr_2            # Col 12: Address_Line2
        ]
        sheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"❌ గూగుల్ షీట్ రిజిస్ట్రేషన్ లోపం: {e}")
        return False