import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime, date, timedelta
from database import load_json, save_json, SESSION_FILE, get_gspread_sheet, HISTORY_FILE

# --- ⚙️ సీక్రెట్ కీ జనరేషన్ సాల్ట్ ---
SECRET_SALT = "RS_ELECTRONIC_2026"

# 🏪 1. పేజీ కాన్ఫిగరేషన్
st.set_page_config(page_title="RS Electronic Ultimate", page_icon="🏪", layout="centered")

# ⚙️ 2. సెషన్ స్టేట్ వేరియబుల్స్ ప్రారంభం
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
if "current_screen" not in st.session_state: st.session_state.current_screen = "📝 Create Challana"

from billing_dashboard import show_billing_dashboard

# గూగుల్ షీట్ కనెక్ట్ చేయడం
try:
    sheet = get_gspread_sheet()
except Exception as e:
    st.error(f"❌ గూగుల్ షీట్ కనెక్షన్ లోపం: {e}")
    st.stop()

# 🔐 3. బ్యాక్‌గ్రౌండ్ ఆటో-లాగిన్ చెకింగ్ (SESSION_FILE లేదా URL ID ద్వారా)
url_params = st.query_params
url_id = url_params.get("id", None)

if not st.session_state.is_logged_in:
    saved_user, saved_pass = None, None
    if os.path.exists(SESSION_FILE):
        try:
            saved = load_json(SESSION_FILE, {})
            saved_user, saved_pass = saved.get("username"), saved.get("password")
        except: pass
        
    try:
        rows = sheet.get_all_values()
        user_found = None
        row_idx = 1
        
        for idx in range(1, len(rows)):
            row = rows[idx]
            if len(row) > 0:
                # ఒకవేళ URL లో ID ఉన్నా లేదా SESSION_FILE లో లాగిన్ వివరాలు ఉన్నా మ్యాచ్ చేస్తుంది
                if (url_id and str(row[0]).strip() == url_id) or (saved_user and str(row[0]).strip() == saved_user):
                    while len(row) < 12: row.append("")
                    user_found = {
                        "Username": row[0], "Password": row[1], "Phone_No": row[2],
                        "Status": row[3], "Key_Type": row[4], "Expiry_Date": row[5],
                        "Profile_Setup_Done": row[6], "Shop_Name": row[7], "Lic_1": row[8],
                        "Lic_2": row[9], "Address_Line1": row[10], "Address_Line2": row[11]
                    }
                    row_idx = idx + 1
                    break
                    
        if user_found:
            if str(user_found.get('Status', '')).strip().upper() not in ["CLOSED", "EXPIRED"]:
                st.session_state.is_logged_in = True
                st.session_state.user_profile = user_found
                st.session_state.user_row_idx = row_idx
    except: pass

# 🚪 4. స్క్రీన్ డిస్‌ప్లే లాజిక్ (లాగిన్ అవ్వకపోతే)
if not st.session_state.is_logged_in:
    # సైడ్‌బార్‌లో అడ్మిన్ లేదా పాత కస్టమర్ల కోసం ఒక రహస్య లాగిన్ ఆప్షన్
    st.sidebar.markdown("### 🔐 Access Control")
    show_login_form = st.sidebar.checkbox("Admin / Existing User Login")

    if show_login_form:
        # --- అడ్మిన్ / పాత యూజర్ లాగిన్ స్క్రీన్ ---
        st.markdown("<h2 style='text-align: center;'>🔒 RS Admin & User Login</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            login_user = st.text_input("User ID / Username").strip()
            login_pass = st.text_input("Password", type="password").strip()
            login_submit = st.form_submit_button("🚀 Login to App", use_container_width=True)
            
            if login_submit:
                if login_user == "admin" and login_pass == "rs2026": # అడ్మిన్ మాస్టర్ లాగిన్
                    st.session_state.is_logged_in = True
                    st.session_state.user_profile = {
                        "Username": "admin", "Key_Type": "Lifetime", "Shop_Name": "RS ELECTRONICS DEVELOPER",
                        "Lic_1": "MASTER-01", "Lic_2": "", "Address_Line1": "ADMIN ZONE", "Address_Line2": "HYDERABAD"
                    }
                    st.success("👑 అడ్మిన్ లాగిన్ విజయవంతమైంది!")
                    st.rerun()
                else:
                    # గూగుల్ షీట్ లో నార్మల్ యూజర్ వెరిఫికేషన్
                    rows = sheet.get_all_values()
                    user_matched = None
                    r_idx = 1
                    for idx in range(1, len(rows)):
                        row = rows[idx]
                        if len(row) > 0 and str(row[0]).strip() == login_user and str(row[1]).strip() == login_pass:
                            while len(row) < 12: row.append("")
                            user_matched = {
                                "Username": row[0], "Password": row[1], "Phone_No": row[2],
                                "Status": row[3], "Key_Type": row[4], "Expiry_Date": row[5],
                                "Profile_Setup_Done": row[6], "Shop_Name": row[7], "Lic_1": row[8],
                                "Lic_2": row[9], "Address_Line1": row[10], "Address_Line2": row[11]
                            }
                            r_idx = idx + 1
                            break
                    if user_matched:
                        st.session_state.is_logged_in = True
                        st.session_state.user_profile = user_matched
                        st.session_state.user_row_idx = r_idx
                        save_json(SESSION_FILE, {"username": login_user, "password": login_pass})
                        st.query_params["id"] = login_user
                        st.success("🎉 లాగిన్ విజయవంతమైంది!")
                        st.rerun()
                    else:
                        st.error("❌ తప్పుడు User ID లేదా Password!")
    else:
        # --- 🌟 ఫస్ట్ స్క్రీన్: కొత్త కస్టమర్ షాప్ ప్రొఫైల్ సెటప్ (FIRST SCREEN) ---
        st.markdown("<h2 style='text-align: center;'>🏪 RS Electronic Ultimate</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Shop Details Setup & Registration (7 Days Free Trial)</p>", unsafe_allow_html=True)
        
        with st.form("shop_registration_form"):
            shop_name = st.text_input("షాప్ పేరు (Shop Name) *").upper().strip()
            phone = st.text_input("మొబైల్ నంబర్ (Phone Number) *").strip()
            
            col1, col2 = st.columns(2)
            with col1:
                lic_1 = st.text_input("లైసెన్స్ నంబర్ 1 (Lic No 1) *").upper().strip()
            with col2:
                lic_2 = st.text_input("లైసెన్స్ నంబర్ 2 (Lic No 2 - Optional)").upper().strip()
                
            addr_1 = st.text_input("అడ్రస్ లైన్ 1 (Address Line 1) *").upper().strip()
            addr_2 = st.text_input("అడ్రస్ లైన్ 2 (Address Line 2) *").upper().strip()
            
            st.markdown("---")
            st.subheader("🖼️ Media Uploads (Optional)")
            logo_file = st.file_uploader("Shop Logo అప్‌లోడ్ చేయండి (PNG)", type=["png"])
            sign_file = st.file_uploader("Owner Signature అప్‌లోడ్ చేయండి (PNG)", type=["png"])
            
            submit_btn = st.form_submit_button("🚀 Create Account & Login To App", type="primary", use_container_width=True)
            
            if submit_btn:
                if not shop_name or not phone or not lic_1 or not addr_1 or not addr_2:
                    st.error("⚠️ దయచేసి స్టార్ (*) గుర్తు ఉన్న వివరాలన్నీ తప్పకుండా నింపండి!")
                else:
                    try:
                        with st.spinner("🔄 ఆటోమేటిక్‌గా System ID జనరేట్ అవుతోంది..."):
                            # 1. ఆటోమేటిక్ సిస్టమ్ ఐడి (Username) జనరేషన్
                            generated_id = f"RS-{uuid.uuid4().hex[:5].upper()}-SYS"
                            default_password = "123" # డిఫాల్ట్ పాస్‌వర్డ్
                            
                            # 2. లోగో మరియు సంతకం సేవ్ చేయడం
                            if logo_file is not None:
                                with open("logo.png", "wb") as f: f.write(logo_file.getbuffer())
                            if sign_file is not None:
                                with open("sign.png", "wb") as f: f.write(sign_file.getbuffer())
                            
                            # 3. డేట్స్ సెట్ చేయడం
                            reg_date_str = datetime.now().strftime("%Y-%m-%d")
                            expiry_date_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                            
                            # 4. గూగుల్ షీట్ లో కొత్త రో యాడ్ చేయడం (మీ షీట్ స్ట్రక్చర్ ప్రకారం)
                            new_row = [
                                generated_id, default_password, phone, "ACTIVE", "Trial", 
                                expiry_date_str, "TRUE", shop_name, lic_1, lic_2, addr_1, addr_2
                            ]
                            sheet.append_row(new_row)
                            
                            # 5. సెషన్ సేవ్ చేసి ఆటో లాగిన్ చేయడం
                            st.session_state.user_profile = {
                                "Username": generated_id, "Password": default_password, "Phone_No": phone,
                                "Status": "ACTIVE", "Key_Type": "Trial", "Expiry_Date": expiry_date_str,
                                "Profile_Setup_Done": "TRUE", "Shop_Name": shop_name, "Lic_1": lic_1,
                                "Lic_2": lic_2, "Address_Line1": addr_1, "Address_Line2": addr_2
                            }
                            st.session_state.is_logged_in = True
                            save_json(SESSION_FILE, {"username": generated_id, "password": default_password})
                            st.query_params["id"] = generated_id
                            
                            st.success("🎉 అకౌంట్ క్రియేట్ అయింది! యాప్ ఓపెన్ అవుతోంది...")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ డేటా సేవ్ చేయడంలో లోపం: {e}")
    st.stop()

# 📆 5. లైసెన్స్ వెరిఫికేషన్ మరియు 7 రోజుల లాక్ లాజిక్
current_user = st.session_state.user_profile

if current_user.get("Key_Type") == "Trial":
    try:
        expiry_date = datetime.strptime(str(current_user.get("Expiry_Date")), "%Y-%m-%d").date()
        days_left = (expiry_date - date.today()).days
        
        # ⚠️ 7 రోజుల ట్రయల్ అయిపోతే యాప్ లాక్ మెసేజ్ చూపిస్తుంది
        if days_left < 0:
            st.error("⏳ మీ 7 రోజుల ఉచిత ట్రయల్ గడువు ముగిసింది!")
            st.warning(f"యాప్‌ను లైఫ్‌టైమ్ యాక్టివేట్ చేయడానికి దయచేసి RS Electronic డెవలపర్‌ను సంప్రదించండి.\n\n🤖 **System ID (Username):** `{current_user.get('Username')}`")
            
            # లైసెన్స్ కీ ఎంటర్ బాక్స్
            input_key = st.text_input("🔑 లైసెన్స్ కీ ఇక్కడ ఎంటర్ చేయండి (Enter Activation Key):").strip().upper()
            
            if st.button("యాక్టివేట్ చేయి (Activate App)", type="primary", use_container_width=True):
                raw_string = f"{current_user.get('Username')}_{SECRET_SALT}"
                correct_key = hashlib.sha256(raw_string.encode()).hexdigest()[:8].upper()
                
                if input_key == correct_key:
                    try:
                        # Key_Type అనేది గూగుల్ షీట్ లో 5వ కాలమ్ (E column)
                        sheet.update_cell(st.session_state.user_row_idx, 5, "Lifetime")
                        st.session_state.user_profile["Key_Type"] = "Lifetime"
                        st.success("🎉 అభినందనలు! మీ యాప్ లైఫ్‌టైమ్ యాక్టివేట్ చేయబడింది.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ అప్‌డేట్ లోపం: {e}")
                else:
                    st.error("❌ తప్పుడు లైసెన్స్ కీ! దయచేసి సరైన కీ ని ఇవ్వండి.")
            st.stop()
        else: 
            st.sidebar.warning(f"⚠️ Trial: {days_left} Days Left")
    except: pass
else:
    st.sidebar.success("🌟 PREMIUM LIFETIME")

# లాగౌట్ బటన్
if st.sidebar.button("🚪 Logout Account"):
    st.session_state.is_logged_in = False
    if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
    st.rerun()

st.sidebar.info(f"🤖 ID: {current_user.get('Username')}")

# 🏁 6. మెయిన్ డాష్‌బోర్డ్ రన్ అవుతుంది
show_billing_dashboard(current_user)