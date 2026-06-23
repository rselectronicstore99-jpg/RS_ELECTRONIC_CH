import streamlit as st
import os
import uuid
import hashlib
from datetime import datetime, date, timedelta
from database import load_json, get_gspread_sheet, HISTORY_FILE
from billing_dashboard import show_billing_dashboard

# --- ⚙️ 1. లైసెన్స్ సెక్యూరిటీ కీ ---
# ఈ సీక్రెట్ కీ ని ఎవరికీ చెప్పకండి. మీ ఓన్ కీజెన్ రాసేటప్పుడు కూడా ఇదే వాడాలి.
SECRET_SALT = "RS_ELECTRONIC_SUPER_SECRET_2026"

# 🏪 2. పేజీ కాన్ఫిగరేషన్
st.set_page_config(page_title="RS Electronic Ultimate", page_icon="🏪", layout="centered")

# ⚙️ 3. సెషన్ స్టేట్ వేరియబుల్స్ ప్రారంభం (Max Bill Logic)
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
if "latest_pdf_path" not in st.session_state: st.session_state.latest_pdf_path = None
if "current_screen" not in st.session_state: st.session_state.current_screen = "📝 Create Challana"

# 🤖 4. యూనిక్ సిస్టమ్ ఐడి ట్రాకింగ్ లాజిక్ (URL Params ద్వారా)
if "system_id" not in st.session_state:
    url_params = st.query_params
    if "id" in url_params:
        st.session_state.system_id = url_params["id"]
    else:
        # కొత్త బ్రౌజర్/ఫోన్ అయితే సరికొత్త ఐడి జెనరేట్ చేసి బ్రౌజర్ లింక్‌లో యాడ్ చేస్తుంది
        new_id = f"RS-{uuid.uuid4().hex[:6].upper()}-SYS"
        st.session_state.system_id = new_id
        st.query_params["id"] = new_id

current_sys_id = st.session_state.system_id

# 🔍 5. గూగుల్ షీట్ నుండి ఈ సిస్టమ్ రికార్డును వెతకడం
user_found = None
try:
    sheet = get_gspread_sheet()
    rows = sheet.get_all_values()
    for idx in range(1, len(rows)):
        row = rows[idx]
        if len(row) > 0 and str(row[0]).strip() == current_sys_id:
            # లిస్ట్ ఇండెక్స్ ఎర్రర్ రాకుండా సేఫ్ సైడ్ పొడిగించడం
            while len(row) < 11: row.append("")
            user_found = {
                "System_ID": row[0], "Shop_Name": row[1], "Phone": row[2],
                "Reg_Date": row[3], "Expiry_Date": row[4], "Status": row[5],
                "License_Key": row[6], "Lic_1": row[7], "Lic_2": row[8],
                "Address_Line1": row[9], "Address_Line2": row[10]
            }
            break
except Exception as e:
    st.error(f"⚠️ గూగుల్ షీట్ కనెక్ట్ అవ్వడంలో లోపం: {e}")
    st.stop()

# 📝 6. కొత్త కస్టమర్ రిజిస్ట్రేషన్ స్క్రీన్ (ఒకవేళ షీట్ లో సిస్టమ్ ఐడి లేకపోతే)
if not user_found:
    st.markdown("<h2 style='text-align: center;'>🏪 RS Electronic Ultimate</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>నూతన షాప్ ప్రొఫైల్ రిజిస్ట్రేషన్ (7 Days Free Trial)</p>", unsafe_allow_html=True)
    
    st.info(f"🤖 మీ సిస్టమ్ నంబర్: `{current_sys_id}`\n\n(భవిష్యత్తులో యాప్ ఓపెన్ చేయడానికి ఈ నంబర్ అవసరం, దీన్ని నోట్ చేసుకోండి!)")
    
    with st.form("shop_registration_form"):
        shop_name = st.text_input("మీ షాప్ పేరు (Shop Name) *").upper().strip()
        phone = st.text_input("మొబైల్ నంబర్ (Phone Number) *").strip()
        
        col1, col2 = st.columns(2)
        with col1:
            lic_1 = st.text_input("లైసెన్స్ నంబర్ 1 (Lic No 1) *").upper().strip()
        with col2:
            lic_2 = st.text_input("లైసెన్స్ నంబర్ 2 (Lic No 2 - Optional)").upper().strip()
            
        addr_1 = st.text_input("అడ్రస్ లైన్ 1 (Address Line 1) *").upper().strip()
        addr_2 = st.text_input("అడ్రస్ లైన్ 2 (Address Line 2) *").upper().strip()
        
        submit_btn = st.form_submit_button("💾 Save & Open App", type="primary", use_container_width=True)
        
        if submit_btn:
            if not shop_name or not phone or not lic_1 or not addr_1 or not addr_2:
                st.error("⚠️ దయచేసి స్టార్ (*) గుర్తు ఉన్న వివరాలన్నీ తప్పకుండా నింపండి!")
            else:
                try:
                    with st.spinner("🔄 గూగుల్ షీట్ లో రికార్డ్ సేవ్ అవుతోంది..."):
                        reg_date_str = datetime.now().strftime("%Y-%m-%d")
                        expiry_date_str = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                        
                        # మీ ఆర్డర్ ప్రకారం షీట్ లో రో యాడ్ చేయడం
                        new_row = [
                            current_sys_id, shop_name, phone, 
                            reg_date_str, expiry_date_str, "Trial", "", 
                            lic_1, lic_2, addr_1, addr_2
                        ]
                        sheet.append_row(new_row)
                        st.success("🎉 ప్రొఫైల్ విజయవంతంగా సేవ్ అయింది! యాప్ ఓపెన్ అవుతోంది...")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ డేటా సేవ్ చేయడంలో లోపం జరిగింది: {e}")
    st.stop()

# 📆 7. పాత కస్టమర్ - లైసెన్స్ మరియు ట్రయల్ పీరియడ్ వెరిఫికేషన్
status = user_found.get("Status", "Trial").strip()
expiry_str = user_found.get("Expiry_Date", "").strip()

# డెవలపర్ వెరిఫికేషన్ కోసం కరెక్ట్ కీ ని లెక్కించడం
raw_string = f"{current_sys_id}{SECRET_SALT}"
secure_hash = hashlib.sha256(raw_string.encode()).hexdigest().upper()
correct_key = f"{secure_hash[:4]}-{secure_hash[4:8]}"

if status == "Trial":
    try:
        expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        days_left = (expiry_date - date.today()).days
        
        if days_left < 0:
            # 7 రోజుల ట్రయల్ అయిపోతే యాప్ లాక్ స్క్రీన్ చూపిస్తుంది
            st.error("⏳ మీ 7 రోజుల ఉచిత ట్రయల్ గడువు ముగిసింది!")
            st.warning(f"యాప్‌ను లైఫ్‌టైమ్ యాక్టివేట్ చేయడానికి దయచేసి RS Electronic డెవలపర్‌ను సంప్రదించండి.\n\n🤖 మీ సిస్టమ్ నంబర్: `{current_sys_id}`")
            
            input_key = st.text_input("లైసెన్స్ కీ ఇక్కడ ఎంటర్ చేయండి (Enter Activation Key):").strip().upper()
            if st.button("యాక్టివేట్ చేయి (Activate App)", type="primary", use_container_width=True):
                if input_key == correct_key:
                    try:
                        rows = sheet.get_all_values()
                        row_to_update = -1
                        for idx, r in enumerate(rows):
                            if len(r) > 0 and r[0].strip() == current_sys_id:
                                row_to_update = idx + 1
                                break
                        if row_to_update != -1:
                            sheet.update_cell(row_to_update, 6, "Lifetime")  # Column 6 = Status
                            sheet.update_cell(row_to_update, 7, input_key)   # Column 7 = License_Key
                            st.success("🎉 అభినందనలు! మీ యాప్ లైఫ్‌టైమ్ యాక్టివేట్ చేయబడింది.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"అప్‌డేట్ లోపం: {e}")
                else:
                    st.error("❌ తప్పుడు లైసెన్స్ కీ! దయచేసి సరైన కీ ని ఇవ్వండి.")
            st.stop()
        else:
            st.sidebar.warning(f"⚠️ Trial: {days_left} Days Left")
    except:
        pass
else:
    st.sidebar.success("🌟 PREMIUM LIFETIME")

# సైడ్ బార్ లో కస్టమర్ ఇన్ఫో డిస్‌ప్లే
st.sidebar.info(f"🤖 ID: {current_sys_id}")

# 🏁 8. మెయిన్ డాష్‌బోర్డ్ రన్ అవ్వడం (billing_dashboard కి పాత ఫార్మాట్ లో డేటా పంపడం)
current_user = {
    "Username": user_found.get("System_ID"),
    "Shop_Name": user_found.get("Shop_Name"),
    "Lic_1": user_found.get("Lic_1"),
    "Lic_2": user_found.get("Lic_2"),
    "Address_Line1": user_found.get("Address_Line1"),
    "Address_Line2": user_found.get("Address_Line2")
}

show_billing_dashboard(current_user)