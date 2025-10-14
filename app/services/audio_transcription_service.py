import openai
import tempfile
import os
from fastapi import UploadFile
from typing import Optional
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
                        #language="en"
                    )

                # Clean up temporary file
                os.unlink(temp_file.name)

                return transcript.text.strip()

        except Exception as e:
            raise Exception(f"Audio transcription failed: {str(e)}")

    def validate_audio_file(self, audio_file: UploadFile) -> bool:
        """Validate that the uploaded file is an audio file"""
        allowed_types = [
            "audio/mpeg", "audio/mp3", "audio/wav", 
            "audio/webm", "audio/m4a", "audio/ogg", "audio/x-m4a"
        ]
        print(f"Validating audio file: {audio_file.content_type}")
        print(f"Allowed types: {allowed_types}")
        print(f"Content type: {audio_file.content_type}")
        print(f"Is allowed: {audio_file.content_type in allowed_types}")
        return audio_file.content_type in allowed_types


                