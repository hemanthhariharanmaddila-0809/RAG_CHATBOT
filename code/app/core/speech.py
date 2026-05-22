import os
import uuid
import logging
import whisper
import httpx
from gtts import gTTS

logger = logging.getLogger(__name__)

class SpeechProcessor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpeechProcessor, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        self.temp_dir = os.getenv("TEMP_AUDIO_PATH", "./temp_audio")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.model = None

    def _load_model(self):
        if self.model is None:
            logger.info("Loading Whisper model...")
            self.model = whisper.load_model("base")
            logger.info("Whisper model loaded.")

    async def transcribe_audio(self, audio_source) -> str:
        self._load_model()
        
        file_path = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.tmp")
        
        try:
            if isinstance(audio_source, str) and audio_source.startswith("http"):
                async with httpx.AsyncClient() as client:
                    response = await client.get(audio_source)
                    response.raise_for_status()
                    audio_bytes = response.content
            else:
                audio_bytes = audio_source

            with open(file_path, "wb") as f:
                f.write(audio_bytes)
                
            logger.info(f"Transcribing audio from {file_path}")
            result = self.model.transcribe(file_path)
            return result["text"].strip()
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    async def text_to_speech(self, text: str) -> bytes:
        try:
            file_path = os.path.join(self.temp_dir, f"{uuid.uuid4().hex}.mp3")
            tts = gTTS(text=text, lang='en')
            tts.save(file_path)
            
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
                
            os.remove(file_path)
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
