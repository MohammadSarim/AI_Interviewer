import streamlit as st
import sys
import torch
import requests
import base64
from streamlit_mic_recorder import mic_recorder
from Resume_Data_Extractor import Data_Extractor as DE
from Voice_transcriber import Voice_Transcriber as VT
from tts_engine import text_to_speech  # 🔊 TTS function

# Fix for torch.classes error in Streamlit
if hasattr(torch, "_classes"):
    sys.modules["torch.classes"] = torch._classes

# Set page config
st.set_page_config(page_title="AI Interviewer", page_icon="🧠")

# Initialize session state variables
if 'parsed_resume' not in st.session_state:
    st.session_state.parsed_resume = None
if 'qa_started' not in st.session_state:
    st.session_state.qa_started = False
if 'last_question' not in st.session_state:
    st.session_state.last_question = ""
if 'question_count' not in st.session_state:
    st.session_state.question_count = 0
if 'audio_trigger' not in st.session_state:
    st.session_state.audio_trigger = False
if 'new_question_ready' not in st.session_state:
    st.session_state.new_question_ready = False

# Sidebar for resume upload
st.sidebar.title("📄 Upload Your Resume")
uploaded_file = st.sidebar.file_uploader("Choose your resume", type=["pdf", "txt", "json", "docx"])

st.title(":brain: AI Interviewer")

if uploaded_file:
    st.success("✅ Resume uploaded successfully!")

    file_text = DE.extract_text(uploaded_file)
    clean_text = DE.preprocess_resume_text(file_text)

    # Show resume preview and parse button in sidebar
    st.sidebar.text_area("📄 Resume Preview", clean_text, height=300)

    if st.sidebar.button("🧠 Parse with LLM"):
        with st.spinner("Sending to Groq backend..."):
            try:
                res = requests.post("http://127.0.0.1:8000/parse-resume/", json={"resume_text": file_text})
                if res.status_code == 200:
                    parsed = res.json()["result"]
                    st.session_state.parsed_resume = parsed
                    st.session_state.qa_started = True
                    st.session_state.last_question = ""
                    st.session_state.question_count = 0
                    st.session_state.audio_trigger = True
                    st.session_state.new_question_ready = True
                    st.success("✅ Resume parsed. Starting interview...")
                    st.rerun()
                else:
                    st.error("❌ Error from backend")
            except Exception as e:
                st.error(f"❌ Backend error: {e}")
else:
    st.info("📎 Please upload your resume from the sidebar to get started.")

# Interview Question Handling
if st.session_state.get("qa_started", False):
    # Generate first question if needed
    if st.session_state.question_count == 0:
        with st.spinner("Generating first question..."):
            qres = requests.post(
                "http://127.0.0.1:8000/generate-question/",
                json={"parsed_resume": st.session_state.parsed_resume}
            )
            if qres.status_code == 200:
                st.session_state.last_question = qres.json()["question"]
                st.session_state.question_count += 1
                st.session_state.new_question_ready = True
                st.session_state.audio_trigger = True
                st.rerun()

    st.markdown("---")
    st.subheader(f"🤖 Question {st.session_state.question_count}")
    question_text = st.session_state.last_question
    st.write(question_text)

    # 🔊 Conditional audio playback
    if st.session_state.audio_trigger:
        try:
            audio_bytes = text_to_speech(question_text)
            b64_audio = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
            <audio autoplay style="display:none;">
                <source src="data:audio/wav;base64,{b64_audio}" type="audio/wav">
            </audio>
            """
            st.components.v1.html(audio_html, height=0)
            
            # Reset audio trigger after playing
            st.session_state.audio_trigger = False
        except Exception as e:
            st.warning(f"⚠️ Failed to speak question: {e}")

    # 🎤 Record user's answer
    audio = mic_recorder(
        start_prompt="🎤 Answer this question",
        stop_prompt="🛑 Stop",
        just_once=True,
        use_container_width=True
    )

    if audio:
        with st.spinner("🧠 Analyzing your answer..."):
            try:
                transcript = VT.convert_and_transcribe(audio["bytes"])
                
                # Get next question
                qres = requests.post(
                    "http://127.0.0.1:8000/next-question/",
                    json={
                        "parsed_resume": st.session_state.parsed_resume,
                        "last_answer": transcript
                    }
                )
                if qres.status_code == 200:
                    st.session_state.last_question = qres.json()["question"]
                    st.session_state.question_count += 1
                    st.session_state.new_question_ready = True
                    st.session_state.audio_trigger = True
                    st.rerun()
                else:
                    st.error("❌ Failed to generate next question")
            except Exception as e:
                st.error(f"❌ Error during transcription or question generation: {e}")