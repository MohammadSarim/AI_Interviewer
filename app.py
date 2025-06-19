import streamlit as st
import sys
import torch
import requests
import base64
import json
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from Voice_transcriber import Voice_Transcriber as VT
from tts_engine import text_to_speech
from db_utils import SessionLocal, Resume

# Fix for torch.classes error in Streamlit
if hasattr(torch, "_classes"):
    sys.modules["torch.classes"] = torch._classes

# Set page config
st.set_page_config(
    page_title="AI Interviewer", 
    page_icon="🧠",
    layout="centered"  # Changed to centered layout
)

st.markdown("""
    <style>
        /* Makes scrollbar appear at browser edge */
        html {
            overflow-y: scroll;
        }
        /* Ensures content doesn't touch scrollbar */
        .stApp {
            padding-right: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    session_vars = {
        'parsed_resume': None,
        'qa_started': False,
        'last_question': "",
        'question_count': 0,
        'audio_trigger': False,
        'new_question_ready': False,
        'candidate_email_input': "",
        'candidate_info': None
    }
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Helper Functions
def parse_resume_data(resume_data):
    if isinstance(resume_data, dict):
        return resume_data
    elif isinstance(resume_data, str):
        try:
            return json.loads(resume_data)
        except json.JSONDecodeError:
            start_idx = resume_data.find('{')
            end_idx = resume_data.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                return json.loads(resume_data[start_idx:end_idx])
            raise ValueError("Invalid JSON format in resume data")
    raise TypeError("Resume data must be either dict or JSON string")

def fetch_candidate(email):
    db = SessionLocal()
    try:
        resume_record = db.query(Resume).filter(Resume.email == email).first()
        if not resume_record:
            return None, "Candidate not found"
        
        parsed_data = parse_resume_data(resume_record.full_data)
        candidate_info = {
            "name": resume_record.name,
            "email": resume_record.email,
            "phone": resume_record.phone,
            "position": resume_record.position,
            "created_at": resume_record.created_at
        }
        
        return {
            "parsed_resume": parsed_data,
            "candidate_info": candidate_info
        }, None
    except Exception as e:
        return None, str(e)
    finally:
        db.close()

# Main App Interface
st.title(":brain: AI Interviewer")

# Email lookup - now in main area
st.subheader("🔍 Retrieve Candidate by Email")
email = st.text_input(
    "Enter Candidate Email", 
    value=st.session_state.candidate_email_input,
    key="email_input"
)

if st.button("Fetch & Start Interview"):
    if not email:
        st.warning("Please enter a candidate email.")
    else:
        candidate_data, error = fetch_candidate(email)
        if error:
            st.error(f"❌ Error: {error}")
        else:
            st.session_state.parsed_resume = candidate_data["parsed_resume"]
            st.session_state.candidate_info = candidate_data["candidate_info"]
            st.session_state.qa_started = True
            st.session_state.candidate_email_input = email
            st.success("✅ Candidate data loaded successfully!")
            st.rerun()

# Show candidate info in main area if available
if st.session_state.candidate_info:
    with st.expander("👤 Candidate Information"):
        st.write(f"**Name**: {st.session_state.candidate_info['name']}")
        st.write(f"**Email**: {st.session_state.candidate_info['email']}")
        st.write(f"**Phone**: {st.session_state.candidate_info['phone']}")
        st.write(f"**Position**: {st.session_state.candidate_info.get('position', 'N/A')}")
        st.write(f"**Added on**: {st.session_state.candidate_info['created_at'].strftime('%Y-%m-%d')}")

if not st.session_state.get("qa_started", False):
    st.info("📎 Please retrieve a candidate by email to start the interview.")

if st.session_state.get("qa_started", False):
    if st.session_state.question_count == 0:
        with st.spinner("Generating first question..."):
            try:
                parsed_resume_str = json.dumps(st.session_state.parsed_resume)
                qres = requests.post(
                    "http://127.0.0.1:8000/generate-question/",
                    json={"parsed_resume": parsed_resume_str}
                )
                if qres.status_code == 200:
                    st.session_state.last_question = qres.json()["question"]
                    st.session_state.question_count += 1
                    st.session_state.new_question_ready = True
                    st.session_state.audio_trigger = True
                    st.rerun()
                else:
                    st.error(f"❌ Failed to generate first question: {qres.text}")
            except Exception as e:
                st.error(f"❌ Error generating question: {str(e)}")

    # Show current question
    st.subheader(f"🤖 Question {st.session_state.question_count}")
    st.write(st.session_state.last_question)

    if st.session_state.audio_trigger:
        try:
            audio_bytes = text_to_speech(st.session_state.last_question)
            b64_audio = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
            </audio>
            """
            st.components.v1.html(audio_html, height=0)
            st.session_state.audio_trigger = False
        except Exception as e:
            st.warning(f"⚠️ Failed to speak question: {e}")

    # Answer section
    st.markdown("---")
    st.subheader("🎤 Your Answer")
    audio = mic_recorder(
        start_prompt="Click to start recording",
        stop_prompt="Click to stop",
        just_once=True,
        use_container_width=True
    )

    if audio:
        with st.spinner("Processing your answer..."):
            try:
                transcript = VT.convert_and_transcribe(audio["bytes"])
                st.write(f"**You said:** {transcript}")
                
                parsed_resume_str = json.dumps(st.session_state.parsed_resume)
                qres = requests.post(
                    "http://127.0.0.1:8000/next-question/",
                    json={
                        "parsed_resume": parsed_resume_str,
                        "last_answer": transcript
                    }
                )
                if qres.status_code == 200:
                    st.session_state.last_question = qres.json()["question"]
                    st.session_state.question_count += 1
                    st.session_state.audio_trigger = True
                    st.rerun()
                else:
                    st.error(f"❌ Failed to generate next question: {qres.text}")
            except Exception as e:
                st.error(f"❌ Error processing answer: {str(e)}")