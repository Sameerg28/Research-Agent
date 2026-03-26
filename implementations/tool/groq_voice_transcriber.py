from __future__ import annotations

import os

from groq import Groq

from config import GROQ_API_KEY
from interfaces.tool import ToolInterface


class GroqVoiceTranscriber(ToolInterface):
    def __init__(self, api_key: str | None = GROQ_API_KEY) -> None:
        self._client = Groq(api_key=api_key)

    def execute(self, input_data: dict | str) -> str:
        if isinstance(input_data, dict):
            audio_file_path = str(input_data.get("audio_file_path", "")).strip()
        else:
            audio_file_path = str(input_data).strip()

        if not audio_file_path:
            return ""

        try:
            with open(audio_file_path, "rb") as file:
                transcription = self._client.audio.transcriptions.create(
                    file=(os.path.basename(audio_file_path), file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                )
            return str(transcription).strip()
        finally:
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
