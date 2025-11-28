import openai
import tempfile
import os
from fastapi import UploadFile
from app.core.config import settings


class AudioTranscriptionService:
    def __init__(self):
        """Initialize OpenAI client for Whisper API"""
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    async def transcribe_audio(self, audio_file: UploadFile) -> str:
        """
        Transcribe audio file to text using OpenAI Whisper API

        Args:
            audio_file: Uploaded audio file (MP3, WAV, etc.)

        Returns:
            Transcribed text as string

        Raises:
            Exception: If transcription fails
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                content = await audio_file.read()
                temp_file.write(content)
                temp_file.flush()

                # Transcribe using Whisper API
                with open(temp_file.name, "rb") as audio_data:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data,
                        # language="en"
                    )

                # Clean up temporary file
                os.unlink(temp_file.name)

                return transcript.text.strip()

        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")

    def validate_audio_file(self, audio_file: UploadFile) -> bool:
        """Validate that the uploaded file is an audio file"""
        allowed_types = [
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/webm",
            "audio/m4a",
            "audio/ogg",
            "audio/x-m4a",
            "audio/x-wav",  # Alternative WAV MIME type
            "audio/vnd.wave",  # Another WAV variant
        ]

        # Check MIME type
        content_type = audio_file.content_type or ""
        if content_type in allowed_types:
            print(f"Audio file validated by MIME type: {content_type}")
            return True

        # Fallback: check file extension if MIME type is missing or not recognized
        filename = audio_file.filename or ""
        allowed_extensions = [".mp3", ".wav", ".webm", ".m4a", ".ogg", ".mp4"]

        if filename:
            file_ext = filename.lower()
            for ext in allowed_extensions:
                if file_ext.endswith(ext):
                    print(
                        f"Audio file validated by extension: {filename} (MIME type was: {content_type})"
                    )
                    return True

        # If content type starts with "audio/" but wasn't in our list, accept it anyway
        # (some browsers might send slightly different MIME types)
        if content_type.startswith("audio/"):
            print(f"Audio file validated by audio/* prefix: {content_type}")
            return True

        print(
            f"Audio file validation failed. Content type: {content_type}, Filename: {filename}"
        )
        return False
