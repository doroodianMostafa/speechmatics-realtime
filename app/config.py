import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SPEECHMATICS_AUTH_TOKEN = os.getenv('SPEECHMATICS_AUTH_TOKEN')

    # Speechmatics Configuration
    SPEECHMATICS_URL = "wss://eu2.rt.speechmatics.com/v2"
    
    # Translation Configuration
    SOURCE_LANGUAGE = "fa"  # Persian
    TARGET_LANGUAGES = ["en", "nl"]  # English & Dutch

    # Audio Configuration
    CHUNK_SIZE = 512
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = "pcm_s16le"

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        if not cls.SPEECHMATICS_AUTH_TOKEN:
            raise ValueError("SPEECHMATICS_AUTH_TOKEN environment variable is not set") 