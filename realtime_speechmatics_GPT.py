# Transcribe with Speechmatics, Translation with GPT- low latency, high accuracy
# ####################################################################
# ####################################################################
# ####################################################################
# ####################################################################

import openai
import os
import pyaudio
import threading
import queue
import time
import speechmatics
from speechmatics.models import (
    ConnectionSettings,
    TranscriptionConfig,
    AudioSettings,
    ServerMessageType
)
from app.models.transcription_model import TranscriptionModel

# =====================
# Configuration
# =====================
# SPEECHMATICS_AUTH_TOKEN = os.getenv("SPEECHMATICS_AUTH_TOKEN")
# if not SPEECHMATICS_AUTH_TOKEN:
#     raise ValueError("Please set the SPEECHMATICS_AUTH_TOKEN environment variable")
SPEECHMATICS_AUTH_TOKEN = "SPEECHMATICS_AUTH_TOKEN"

CONNECTION_URL = "wss://eu2.rt.speechmatics.com/v2"
SOURCE_LANGUAGE = "fa"   # Persian
TARGET_LANGUAGES = ["en", "nl"]  # English & Dutch

CHUNK_SIZE = 512
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = 2

# Set OpenAI API key from environment variable
# openai.api_key = os.getenv("OPENAI_API_KEY")
# if not openai.api_key:
#     raise ValueError("Please set the OPENAI_API_KEY environment variable")
openai.api_key = "api_key"


# =====================
# Global Variables
# =====================
audio_queue = queue.Queue()
transcript_buffer = ""
print_lock = threading.Lock()
transcription_model = TranscriptionModel()  # Initialize the model

# =====================
# GPT Translation
# =====================
def translate_with_gpt4(text: str, source_lang: str, target_langs: list) -> dict:
    """
    Single API call for all target languages
    Returns dictionary of {lang: translation}
    """
    try:
        langs_str = ", ".join(target_langs)
        system_prompt = (
            f"Translate this {source_lang} text to {langs_str}. "
            f"Output format: 'lang_code: translation' per line. "
            f"No extra text."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
        )
        translated_output = response["choices"][0]["message"]["content"].strip()
        return parse_translations(translated_output, target_langs)
    except Exception as e:
        return {lang: f"<Error: {e}>" for lang in target_langs}

def parse_translations(output: str, target_langs: list) -> dict:
    """Parse GPT's response into translation dictionary"""
    translations = {}
    for line in output.split('\n'):
        if ': ' in line:
            lang, trans = line.split(': ', 1)
            lang = lang.strip().lower()
            if lang in target_langs:
                translations[lang] = trans.strip()
    # Add missing languages
    for lang in target_langs:
        if lang not in translations:
            translations[lang] = f"<Missing {lang} translation>"
    return translations

# =====================
# Speechmatics Client
# =====================
ws = speechmatics.client.WebsocketClient(
    ConnectionSettings(
        url=CONNECTION_URL,
        auth_token=SPEECHMATICS_AUTH_TOKEN
    )
)

def handle_final_transcript(msg):
    global transcript_buffer
    final_text = msg['metadata']['transcript'].strip()
    transcript_buffer += " " + final_text
    
    # Trigger translation when natural breakpoint detected
    if final_text.endswith(('.', '!', '?')) or len(transcript_buffer.split()) >= 10:  # Slightly lower word threshold
        persian_text = transcript_buffer.strip()
        transcript_buffer = ""  # Immediate reset
        
        with print_lock:
            print(f"\n[Original] {persian_text}")

        # Process translation without blocking
        def process_translation():
            start_time = time.time()
            translations = translate_with_gpt4(persian_text, "Persian", TARGET_LANGUAGES)
            duration = time.time() - start_time
            
            with print_lock:
                for lang in TARGET_LANGUAGES:
                    print(f"[{lang.upper()}] {translations.get(lang, '')}")
                print(f"Translation took {duration:.2f}s\n")
            
            # Save to CSV
            try:
                transcription_model.save_transcription(persian_text, translations)
                print("Saved transcription to CSV file")
            except Exception as e:
                print(f"Error saving to CSV: {e}")
        
        threading.Thread(target=process_translation).start()

# Only register final transcript handler
ws.add_event_handler(
    event_name=ServerMessageType.AddTranscript,
    event_handler=handle_final_transcript
)

# Speechmatics configuration without partials
settings = AudioSettings(
    encoding="pcm_s16le",
    sample_rate=SAMPLE_RATE,
    chunk_size=CHUNK_SIZE
)

config = TranscriptionConfig(
    language=SOURCE_LANGUAGE,
    enable_partials=False,  # Partials disabled
    max_delay=2.5,  # More aggressive finalization
    operating_point="enhanced"
)

# =====================
# Audio Capture (unchanged)
# =====================
class QueueStream:
    def __init__(self, q):
        self.queue = q
        self.running = True

    def read(self, num_bytes):
        while self.running:
            try:
                data = self.queue.get(timeout=2)
                if data is None:
                    self.running = False
                    return b""
                return data
            except queue.Empty:
                continue
        return b""

def capture_audio():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )
    print("Microphone active - start speaking")
    try:
        while True:
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_queue.put(data)
    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        p.terminate()
        audio_queue.put(None)

# =====================
# Main Execution
# =====================
if __name__ == "__main__":
    print("Live Persian-to-Multilingual Translator")
    print("=======================================")
    
    audio_thread = threading.Thread(target=capture_audio)
    audio_thread.daemon = True
    audio_thread.start()

    time.sleep(0.5)  # Shorter initial delay

    try:
        ws.run_synchronously(QueueStream(audio_queue), config, settings)
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if transcript_buffer:
            translations = translate_with_gpt4(transcript_buffer, "Persian", TARGET_LANGUAGES)
            print("\nFinal translations:")
            for lang in TARGET_LANGUAGES:
                print(f"[{lang.upper()}] {translations.get(lang, '')}")
