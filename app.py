import streamlit as st
import os
from datetime import datetime, date
from database import load_json, SESSION_FILE, get_gspread_sheet, HISTORY_FILE

# 🏪 1. పేజీ కాన్ఫిగరేషన్
st.set_page_config(page_title="RS Electronic Ultimate", page_icon="🏪", layout="centered")

# ⚙️ 2. సెషన్ స్టేట్ వేరియబుల్స్ ప్రారంభం (Max Bill Logic అప్లై చేయబడింది)
if "bill_no" not in st.session_state:
    history_records = load_json(HISTORY_FILE, [])
    max_bill = 999
    for r in history_records:
        try:
            val = int(r.get('bill_no', ''))
            if val > max_bill:
                max_bill = val
        except: pass
    st.session_state.bill_no = str(max_bill + 1)

if "manual_date" not in st.session_state: st.session_state.manual_date = datetime.now().strftime('%d-%m-%Y')
if "cust_name" not in st.session_state: st.session_state.cust_name = ""
if "cust_phone" not in st.session_state: st.session_state.cust_phone = ""
if "cust_pro" not in st.session_state: st.session_state.cust_pro = ""
if "cust_area" not in st.session_state: st.session_state.cust_area = ""
if "bill_items" not in st.session_state: st.session_state.bill_items = []
if "is_logged_in" not in st.session_state: st.session_state.is_logged_in = False
if "latest_pdf_path" not in st.session_state: st.session_state.latest_pdf_path = None

# నావిగేషన్ కంట్రోల్
if "current_screen" not in st.session_state: st.session_state.current_screen = "📝 Create Challana"

from auth_manager import login_or_register_screen, shop_profile_setup_screen
from billing_dashboard import show_billing_dashboard

# 🔐 3. బ్యాక్‌గ్రౌండ్ ఆటో-లాగిన్ చెкиంగ్
if not st.session_state.is_logged_in and os.path.exists(SESSION_FILE):
    try:
        saved = load_json(SESSION_FILE, {})
        s_user, s_pass = saved.get("username"), saved.get("password")
        if s_user and s_pass:
            sheet = get_gspread_sheet()
            rows = sheet.get_all_values()
            user_found = None
            row_idx = 1
            for idx in range(1, len(rows)):
                row = rows[idx]
                if len(row) > 0 and str(row[0]).strip() == s_user:
                    while len(row) < 12: row.append("")
                    user_found = {
                        "Username": row[0], "Password": row[1], "Phone_No": row[2],
                        "Status": row[3], "Key_Type": row[4], "Expiry_Date": row[5],
                        "Profile_Setup_Done": row[6], "Shop_Name": row[7], "Lic_1": row[8],
                        "Lic_2": row[9], "Address_Line1": row[10], "Address_Line2": row[11]
                    }
                    row_idx = idx + 1
                    break
            if user_found and str(user_found.get('Password')).strip() == s_pass:
                if str(user_found.get('Status', '')).strip().upper() not in ["CLOSED", "EXPIRED"]:
                    st.session_state.is_logged_in = True
                    st.session_state.user_profile = user_found
                    st.session_state.user_row_idx = row_idx
    except: pass

if not st.session_state.is_logged_in:
    login_or_register_screen()
    st.stop()

current_user = st.session_state.user_profile

# 📆 లైసెన్స్ వెరిఫికేషన్ సైడ్‌బార్
if current_user.get("Key_Type") == "Trial":
    try:
        expiry_date = datetime.strptime(str(current_user.get("Expiry_Date")), "%Y-%m-%d").date()
        days_left = (expiry_date - date.today()).days
        if days_left < 0:
            st.error("⏳ మీ ట్రయల్ ముగిసింది!")
            st.stop()
        else: st.sidebar.warning(f"⚠️ Trial: {days_left} Days Left")
    except: pass
else:
    st.sidebar.success("🌟 PREMIUM LIFETIME")

if st.sidebar.button("🚪 Logout"):
    st.session_state.is_logged_in = False
    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
    st.rerun()

if str(current_user.get("Profile_Setup_Done")).strip().upper() != "TRUE":
    shop_profile_setup_screen()
    st.stop()

# 🏁 మెయిన్ డాష్‌బోర్డ్ రన్ అవుతుంది
show_billing_dashboard(current_user)