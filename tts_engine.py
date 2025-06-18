import pyttsx3
import tempfile
import os

def text_to_speech(text: str) -> bytes:
    """Convert text to speech with improved pyttsx3 settings"""
    engine = pyttsx3.init()
    
    # Get available voices and select the best one
    voices = engine.getProperty('voices')
    
    # Prefer Microsoft David Desktop if available (clearer voice)
    preferred_voices = [
        "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0",
        "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
    ]
    
    for voice in voices:
        if any(v in voice.id for v in preferred_voices):
            engine.setProperty('voice', voice.id)
            break
    
    # Optimized speech parameters
    engine.setProperty('rate', 170)  # Slightly faster than normal (180-200 words/min)
    engine.setProperty('volume', 1.0)
    engine.setProperty('pitch', 110)  # Slightly higher pitch for clarity
    
    # Add pauses for punctuation
    engine.setProperty('pause.between.sentences', 150)
    engine.setProperty('pause.between.words', 50)
    
    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
    
    try:
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        
        # Read the generated audio
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes
    finally:
        # Clean up
        try:
            os.remove(temp_path)
        except:
            pass