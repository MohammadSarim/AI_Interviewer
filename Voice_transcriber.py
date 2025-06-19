import tempfile
import subprocess
import whisper
import os

class Voice_Transcriber:
    @staticmethod
    def convert_and_transcribe(audio_bytes):
        # Save the raw WebM audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as raw_audio_file:
            raw_audio_file.write(audio_bytes)
            raw_audio_path = raw_audio_file.name

        # Temporary file for converted PCM WAV format
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as converted_audio_file:
            pcm_audio_path = converted_audio_file.name

        try:
            # Convert the audio using ffmpeg
            subprocess.run([
                "ffmpeg", "-y",
                "-i", raw_audio_path,
                "-ar", "16000",  
                "-ac", "1",     
                "-f", "wav",
                pcm_audio_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Load Whisper model and transcribe
            model = whisper.load_model("tiny")
            result = model.transcribe(pcm_audio_path)
            return result["text"]

        finally:
            # Clean up temp files
            os.remove(raw_audio_path)
            os.remove(pcm_audio_path)
