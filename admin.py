import streamlit as st
import requests
from Resume_Data_Extractor import Data_Extractor as DE
from db_utils import save_parsed_resume
from auth import login_page

def main_admin_panel():
    st.set_page_config(page_title="Admin Panel", page_icon="🛠️", layout="wide")
    
    # Sidebar
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.admin['full_name']}")
        if st.button("🚪 Logout"):
            st.session_state["show_admin_panel"] = False
            st.session_state["authenticated"] = False
            st.session_state.pop("admin", None)
            st.rerun()
    
    st.header("📄 Resume Upload Portal")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name*")
        email = st.text_input("Email*")
    with col2:
        phone = st.text_input("Phone Number*")
        position = st.text_input("Position Applied For")

    uploaded_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)*", type=["pdf", "docx", "txt"])

    if uploaded_file and name and email and phone:
        file_text = DE.extract_text(uploaded_file)

        with st.expander("View Extracted Resume Text"):
            st.text_area("Raw Text", value=file_text, height=200, label_visibility="collapsed")

        if st.button("Process Resume"):
            with st.spinner("Analyzing resume..."):
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/parse-resume/",
                        json={"resume_text": file_text},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        parsed_data = response.json()
                        full_data = {
                            "contact_info": {
                                "name": name,
                                "email": email,
                                "phone": phone,
                                "position": position,
                                "processed_by": st.session_state.admin["username"]
                            },
                            "parsed_resume": parsed_data,
                            "raw_text": file_text
                        }

                        success, message = save_parsed_resume(full_data, primary_key=email)
                        if success:
                            st.success(f"Resume processed successfully for {email}!")
                            st.json(parsed_data)
                        else:
                            st.error(message)
                    else:
                        st.error(f"API Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Processing failed: {str(e)}")
    elif uploaded_file:
        st.warning("Please fill all required fields (*)")
    else:
        st.info("Please fill candidate information and upload a resume")

# Main app logic
if "show_admin_panel" not in st.session_state:
    st.session_state["show_admin_panel"] = False
    st.session_state["authenticated"] = False

if st.session_state.get("show_admin_panel") and st.session_state.get("authenticated"):
    main_admin_panel()
else:
    st.set_page_config(page_title="Admin Portal", page_icon="🔒")
    st.title("Admin Portal")
    login_page()