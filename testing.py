import streamlit as st
import sys
import torch
import requests
import sounddevice as sd
import wavio
import speech_recognition as sr
import tempfile
import os

from backend import Resume_Data_Extractor as RE  # Make sure this file exists with correct functions

# ✅ Fix for torch.classes issue in Streamlit
if hasattr(torch, "_classes"):
    sys.modules["torch.classes"] = torch._classes

# ✅ Page configuration
st.set_page_config(page_title="AI Interviewer", page_icon="🧠")

# ================== 📤 Resume Upload ==================
st.sidebar.title("📤 Upload Your Resume")
uploaded_file = st.sidebar.file_uploader("Choose your resume", type=["pdf", "txt", "json", "docx"])

st.title("🧠 AI Interviewer")

# ================== 📄 Resume Parsing ==================
if uploaded_file:
    st.success("✅ Resume uploaded successfully!")

    file_text = RE.extract_text(uploaded_file)
    clean_text = RE.preprocess_resume_text(file_text)

    st.text_area("📄 Resume Preview", clean_text, height=300)

    if st.button("🧠 Parse with LLM"):
        with st.spinner("Sending to Groq backend..."):
            try:
                res = requests.post("http://127.0.0.1:8000/parse-resume/", json={"resume_text": file_text})
                if res.status_code == 200:
                    parsed = res.json()["result"]
                    st.subheader("🔍 Extracted Information")
                    st.code(parsed, language="json")
                else:
                    st.error("❌ Error from backend")
            except Exception as e:
                st.error(f"❌ Backend error: {e}")
else:
    st.info("📎 Please upload your resume from the sidebar to get started.")

# ================== 🎙️ Voice Recorder (No Conversion Needed) ==================
st.markdown("---")
st.subheader("🎙️ Record Your Answer")

duration = st.slider("Select Recording Duration (seconds)", min_value=1, max_value=10, value=5)

if st.button("🎤 Start Recording"):
    st.info("🔴 Recording... Please speak clearly.")
    fs = 44100  # Sampling rate
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # Save to a temporary WAV file (PCM format)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        wavio.write(tmpfile.name, audio, fs, sampwidth=2)
        audio_path = tmpfile.name

    st.success("✅ Recording complete.")
    st.audio(audio_path, format="audio/wav")

    # ================== 📝 Transcription ==================
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        recorded_audio = recognizer.record(source)

    try:
        with st.spinner("🧠 Transcribing your response..."):
            text = recognizer.recognize_google(recorded_audio)
            st.subheader("📝 Transcription")
            st.write(text)
    except sr.UnknownValueError:
        st.error("❌ Could not understand the audio.")
    except sr.RequestError:
        st.error("❌ Could not reach the Google API.")
    finally:
        os.remove(audio_path)
