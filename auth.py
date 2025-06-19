from db_utils import AdminUser, SessionLocal, create_admin_user
from werkzeug.security import check_password_hash
import streamlit as st
import datetime

def authenticate(username: str, password: str) -> bool:
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(
            AdminUser.username == username,
            AdminUser.is_active == True
        ).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            st.session_state["admin"] = {
                "username": admin.username,
                "full_name": admin.full_name,
                "api_key": admin.api_key
            }
            st.session_state["authenticated"] = True
            st.session_state["admin"]["authenticated"] = True
            
            admin.last_login = datetime.datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False
    finally:
        db.close()

def registration_form():
    with st.form("Registration Form"):
        st.subheader("New Admin Registration")
        username = st.text_input("Username*")
        password = st.text_input("Password*", type="password", 
                               help="Minimum 8 characters")
        confirm_pw = st.text_input("Confirm Password*", type="password")
        full_name = st.text_input("Full Name*")
        
        if st.form_submit_button("Register"):
            if not all([username, password, confirm_pw, full_name]):
                st.error("Please fill all required fields")
                return False
                
            if password != confirm_pw:
                st.error("Passwords don't match")
                return False
                
            if len(password) < 8:
                st.error("Password must be at least 8 characters")
                return False
                
            success, message = create_admin_user(
                username=username,
                password=password,
                full_name=full_name
            )
            
            if success:
                st.success("Registration successful! Please login")
                st.session_state["just_registered"] = True
                return True
            else:
                st.error(message)
                return False
    return False

def login_page():
    if st.session_state.get("just_registered"):
        st.session_state.pop("just_registered")
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            st.info("Please login with your new credentials")
    else:
        login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        with st.form("Login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if authenticate(username, password):
                    st.session_state["show_admin_panel"] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with register_tab:
        if registration_form():
            st.rerun()