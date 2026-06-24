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

# --- లైసెన్స్ సెక్యూరిటీ కీ ---
SECRET_SALT = "RS_ELECTRONIC_SUPER_SECRET_2026"

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
        raw_creds = st.secrets["google_credentials"]
        
        # 💡 ఒకవేళ టెక్స్ట్ (String) రూపంలో ఉంటే JSON గా మారుస్తుంది, లేదంటే dict గా మారుస్తుంది
        if isinstance(raw_creds, str):
            creds_dict = json.loads(raw_creds)
        else:
            creds_dict = dict(raw_creds)
            
        return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except Exception as e:
        st.error(f"❌ కీ రీడింగ్ లోపం: {e}")
        return None

def get_google_credentials():
    return get_service_account_creds()

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
    try:
        if "google_credentials" not in st.secrets:
            st.error("Error: Streamlit Secrets లో 'google_credentials' లేదు!")
            return None
            
        raw_creds = st.secrets["google_credentials"]
        
        # 💡 ఇక్కడ కూడా టెక్స్ట్ మరియు డిక్షనరీ రెండింటినీ సేఫ్ గా హ్యాండిల్ చేస్తున్నాము
        if isinstance(raw_creds, str):
            creds_dict = json.loads(raw_creds)
        else:
            creds_dict = dict(raw_creds)
            
        gc = gspread.service_account_from_dict(creds_dict)
        sheet = gc.open("RS_Custmores").sheet1 
        return sheet
    except Exception as e:
        st.error(f"❌ గూగుల్ షీట్ ఓపెన్ చేయడంలో లోపం: {e}")
        return None

def load_json(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r") as f: return json.load(f)
    return default_val

def save_json(filename, data):
    with open(filename, "w") as f: json.dump(data, f, indent=4)

# --- 🆕 కొత్త లైసెన్స్ సిస్టమ్ ఫంక్షన్లు ---

def generate_system_id():
    """కొత్త కస్టమర్ కోసం రాండమ్ సిస్టమ్ నంబర్ క్రియేట్ చేస్తుంది"""
    return f"RS-{uuid.uuid4().hex[:6].upper()}-SYS"

def calculate_valid_key(system_id):
    """సిస్టమ్ నంబర్ ఆధారంగా డెవలపర్ కరెక్ట్ కీ ని లెక్కిస్తుంది"""
    import hashlib
    raw_string = f"{system_id}{SECRET_SALT}"
    secure_hash = hashlib.sha256(raw_string.encode()).hexdigest().upper()
    return f"{secure_hash[:4]}-{secure_hash[4:8]}"

def get_customer_by_sys_id(system_id):
    """గూగుల్ షీట్ నుండి సిస్టమ్ ఐడి రికార్డును తెస్తుంది"""
    try:
        sheet = get_gspread_sheet()
        if not sheet: return None
        all_records = sheet.get_all_records()
        for row in all_records:
            if str(row.get('System_ID')).strip() == system_id:
                return row
        return None
    except:
        return None

def register_system_customer(system_id, shop_name, phone, lic_1, lic_2, addr_1, addr_2):
    """కొత్త కస్టమర్ ప్రొఫైల్ మొత్తాన్ని గూగుల్ షీట్ లో ఒకేసారి సేవ్ చేస్తుంది"""
    try:
        sheet = get_gspread_sheet()
        if not sheet: return False
        
        reg_date = datetime.now()
        expiry_date = reg_date + timedelta(days=7) # 7 రోజుల ఉచిత ట్రయల్
        
        new_row = [
            system_id,
            shop_name,
            phone,
            reg_date.strftime("%Y-%m-%d"),
            expiry_date.strftime("%Y-%m-%d"),
            "Trial",       # Status
            "",            # License_Key (ప్రస్తుతానికి ఖాళీ)
            lic_1,
            lic_2,
            addr_1,
            addr_2
        ]
        sheet.append_row(new_row)
        return True
    except Exception as e:
        st.error(f"రిజిస్ట్రేషన్ లోపం: {e}")
        return False

def activate_system_license(system_id, license_key):
    """లైసెన్స్ కీ వెరిఫై చేసి గూగుల్ షీట్ లో 'Lifetime' గా అప్‌డేట్ చేస్తుంది"""
    try:
        sheet = get_gspread_sheet()
        if not sheet: return False
        
        if license_key != calculate_valid_key(system_id):
            return False
            
        all_records = sheet.get_all_records()
        for index, row in enumerate(all_records, start=2):
            if str(row.get('System_ID')).strip() == system_id:
                sheet.update_cell(index, 6, "Lifetime")     # 6వ కాలమ్ Status
                sheet.update_cell(index, 7, license_key)   # 7వ కాలమ్ License_Key
                return True
        return False
    except Exception as e:
        st.error(f"యాక్టివేషన్ లోపం: {e}")
        return False
