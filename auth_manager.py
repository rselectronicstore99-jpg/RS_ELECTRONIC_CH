import streamlit as st
from datetime import date, datetime, timedelta
import os
from database import get_gspread_sheet, save_json, load_json, SESSION_FILE

def login_or_register_screen():
    st.markdown("<h2 style='text-align: center;'>🏪 RS Electronic Ultimate</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Sign In / New User Auto-Registration</p>", unsafe_allow_html=True)
    
    with st.form("auth_form"):
        user_input = st.text_input("👤 User ID *").strip()
        pass_input = st.text_input("🔒 Password *", type="password").strip()
        submit_btn = st.form_submit_button("🚀 Login / Register", use_container_width=True)
        
        if submit_btn:
            if not user_input or not pass_input:
                st.error("⚠️ దయచేసి వివరాలన్నీ ఎంటర్ చేయండి!")
            else:
                try:
                    sheet = get_gspread_sheet()
                    rows = sheet.get_all_values()
                    user_found = None
                    row_idx = 1  
                    
                    for idx in range(1, len(rows)):
                        row = rows[idx]
                        if len(row) > 0 and str(row[0]).strip() == user_input:
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
                        if str(user_found.get('Password')).strip() == pass_input:
                            if str(user_found.get('Status', '')).strip().upper() in ["CLOSED", "EXPIRED"]:
                                st.error("⚠️ మీ అకౌంట్ బ్లాక్ చేయబడింది!")
                            else:
                                st.session_state.is_logged_in = True
                                st.session_state.user_profile = user_found
                                st.session_state.user_row_idx = row_idx
                                save_json(SESSION_FILE, {"username": user_input, "password": pass_input})
                                st.success("✅ లాగిన్ విజయవంతమైంది!")
                                st.rerun()
                        else:
                            st.error("❌ పాస్‌వర్డ్ తప్పు!")
                    else:
                        expiry_str = str(date.today() + timedelta(days=7))
                        new_row = [user_input, pass_input, pass_input, "ACTIVE", "Trial", expiry_str, "FALSE", "", "", "", "", ""]
                        sheet.append_row(new_row)
                        
                        st.session_state.is_logged_in = True
                        st.session_state.user_row_idx = len(rows) + 1
                        st.session_state.user_profile = {
                            "Username": user_input, "Password": pass_input, "Phone_No": pass_input,
                            "Status": "ACTIVE", "Key_Type": "Trial", "Expiry_Date": expiry_str,
                            "Profile_Setup_Done": "FALSE", "Shop_Name": "", "Lic_1": "", "Lic_2": "",
                            "Address_Line1": "", "Address_Line2": ""
                        }
                        save_json(SESSION_FILE, {"username": user_input, "password": pass_input})
                        st.success("🎉 అకౌంట్ క్రియేట్ అయింది! 7 రోజుల ట్రయల్ యాక్టివేట్ చేయబడింది.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ సర్వర్ కనెక్షన్ ఎర్రర్: {e}")

def shop_profile_setup_screen():
    st.title("🏪 Setup Your Shop Profile")
    st.info("ఇది ఒకే ఒక్క సారి అడిగే ప్రొఫైల్ సెటప్.")
    
    with st.form("shop_details_form"):
        col1, col2 = st.columns(2)
        with col1:
            shop_name = st.text_input("మీ షాప్ పేరు *").upper()
            lic_1 = st.text_input("లైసెన్స్ నంబర్ 1 *").upper()
        with col2:
            lic_2 = st.text_input("లైసెన్స్ నంబర్ 2 (Optional)").upper()
            addr_1 = st.text_input("అడ్రస్ లైన్ 1 *").upper()
        addr_2 = st.text_input("అడ్రస్ లైన్ 2 *").upper()
        save_btn = st.form_submit_button("💾 Save Profile Details & Open App", type="primary")
        
        if save_btn:
            if not shop_name or not lic_1 or not addr_1 or not addr_2:
                st.error("⚠️ దయచేసి వివరాలన్నీ తప్పకుండా నింపండి!")
            else:
                try:
                    with st.spinner("🔄 సేవ్ అవుతోంది..."):
                        sheet = get_gspread_sheet()
                        row_idx = st.session_state.user_row_idx
                        
                        sheet.update_cell(row_idx, 7, "TRUE")       
                        sheet.update_cell(row_idx, 8, shop_name)    
                        sheet.update_cell(row_idx, 9, lic_1)        
                        sheet.update_cell(row_idx, 10, lic_2)       
                        sheet.update_cell(row_idx, 11, addr_1)      
                        sheet.update_cell(row_idx, 12, addr_2)      
                        
                        st.session_state.user_profile["Profile_Setup_Done"] = "TRUE"
                        st.session_state.user_profile["Shop_Name"] = shop_name
                        st.session_state.user_profile["Lic_1"] = lic_1
                        st.session_state.user_profile["Lic_2"] = lic_2
                        st.session_state.user_profile["Address_Line1"] = addr_1
                        st.session_state.user_profile["Address_Line2"] = addr_2
                        st.success("🎉 షాప్ ప్రొఫైల్ సేవ్ అయింది!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ ప్రొఫైల్ సేవ్ చేయడంలో లోపం: {e}")