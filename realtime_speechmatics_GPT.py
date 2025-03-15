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

# =====================
# Configuration
# =====================
SPEECHMATICS_AUTH_TOKEN = os.getenv("SPEECHMATICS_AUTH_TOKEN")
if not SPEECHMATICS_AUTH_TOKEN:
    raise ValueError("Please set the SPEECHMATICS_AUTH_TOKEN environment variable")

CONNECTION_URL = "wss://eu2.rt.speechmatics.com/v2"
SOURCE_LANGUAGE = "fa"   # Persian
TARGET_LANGUAGES = ["en", "nl"]  # English & Dutch

CHUNK_SIZE = 512
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = 2

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# =====================
# Global Variables
# =====================
audio_queue = queue.Queue()
transcript_buffer = ""
print_lock = threading.Lock()

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


# # Transcribe with Speechmatics, Translation with GPT-4:AddPartialTranscript
# ####################################################################
# ####################################################################
# ####################################################################
# ####################################################################
# import openai
# import os
# import pyaudio
# import threading
# import queue
# import time
# import speechmatics
# from speechmatics.models import (
#     ConnectionSettings,
#     TranscriptionConfig,
#     AudioSettings,
#     ServerMessageType
# )

# # =====================
# # Configuration
# # =====================
# SPEECHMATICS_AUTH_TOKEN = "SPEECHMATICS_AUTH_TOKEN"
# CONNECTION_URL = "wss://eu2.rt.speechmatics.com/v2"

# SOURCE_LANGUAGE = "fa"   # Persian
# TARGET_LANGUAGES = ["en", "nl"]  # e.g., English & Dutch

# CHUNK_SIZE = 1024
# SAMPLE_RATE = 44100
# CHANNELS = 1
# FORMAT = pyaudio.paInt16
# SAMPLE_WIDTH = 2

# # GPT-4 Key (Best to set via environment var)
# openai.api_key = ""

# # =====================
# # Global Variables
# # =====================
# audio_queue = queue.Queue()
# transcript_buffer = ""  # accumulates final transcripts

# # =====================
# # GPT Translation
# # =====================
# def translate_with_gpt4(text: str, source_lang: str, target_lang: str) -> str:
#     """
#     Use OpenAI's GPT-4 to translate from source_lang to target_lang.
#     """
#     try:
#         system_prompt = (
#             f"You are a helpful translation assistant. "
#             f"Translate the following text from {source_lang} to {target_lang}. "
#             f"Output only the translation, no extra commentary."
#         )
#         user_message = f"{text}"

#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_message}
#             ],
#             temperature=0.0,
#         )
        
#         translated_text = response["choices"][0]["message"]["content"].strip()
#         return translated_text

#     except Exception as e:
#         return f"<GPT Translation Error: {e}>"

# # =====================
# # Speechmatics Client
# # =====================
# ws = speechmatics.client.WebsocketClient(
#     ConnectionSettings(
#         url=CONNECTION_URL,
#         auth_token=SPEECHMATICS_AUTH_TOKEN
#     )
# )

# # PARTIAL TRANSCRIPT HANDLER
# def handle_partial_transcript(msg):
#     """
#     Called whenever a partial transcript is received.
#     We'll show partial Persian text but NOT translate yet.
#     """
#     partial_text = msg['metadata']['transcript'].strip()
#     # Display partial text to user
#     print(f"[Partial (fa)] {partial_text}")

# # FINAL TRANSCRIPT HANDLER
# def handle_final_transcript(msg):
#     """
#     Called when a final transcript is received.
#     We'll accumulate and then pass to GPT if punctuation or word count threshold is met.
#     """
#     global transcript_buffer
#     final_text = msg['metadata']['transcript'].strip()
#     transcript_buffer += " " + final_text
    
#     # Check punctuation or length to decide if we translate now
#     if final_text.endswith(('.', '!', '?')) or len(transcript_buffer.split()) > 10:
#         persian_text = transcript_buffer.strip()
        
#         # Print final in Persian
#         print(f"[Final (fa)] {persian_text}")

#         # Translate to target languages with GPT-4
#         for lang in TARGET_LANGUAGES:
#             translated_text = translate_with_gpt4(persian_text, "Persian", lang)
#             print(f"[{lang}] {translated_text}")

#         # Reset buffer after translation
#         transcript_buffer = ""

# # REGISTER EVENT HANDLERS
# ws.add_event_handler(
#     event_name=ServerMessageType.AddPartialTranscript,
#     event_handler=handle_partial_transcript
# )
# ws.add_event_handler(
#     event_name=ServerMessageType.AddTranscript,
#     event_handler=handle_final_transcript
# )

# # AUDIO SETTINGS FOR SPEECHMATICS
# settings = AudioSettings(
#     encoding="pcm_s16le",
#     sample_rate=SAMPLE_RATE,
#     chunk_size=CHUNK_SIZE
# )

# config = TranscriptionConfig(
#     language=SOURCE_LANGUAGE,
#     enable_partials=True,  # Enable partial transcripts
#     max_delay=5,
#     operating_point="enhanced"
# )

# # =====================
# # Audio Capture
# # =====================
# class QueueStream:
#     def __init__(self, q):
#         self.queue = q
#         self.running = True

#     def read(self, num_bytes):
#         while self.running:
#             try:
#                 data = self.queue.get(timeout=2)
#                 if data is None:
#                     self.running = False
#                     return b""
#                 if len(data) > 0:
#                     return data
#             except queue.Empty:
#                 continue
#         return b""

# def capture_audio():
#     p = pyaudio.PyAudio()
#     stream = p.open(
#         format=FORMAT,
#         channels=CHANNELS,
#         rate=SAMPLE_RATE,
#         input=True,
#         frames_per_buffer=CHUNK_SIZE
#     )
#     print("Capturing audio from microphone... Speak now (in Persian)!")
#     try:
#         while True:
#             data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
#             audio_queue.put(data)
#     except KeyboardInterrupt:
#         stream.stop_stream()
#         stream.close()
#         p.terminate()
#         audio_queue.put(None)
#         print("\nStopped capturing audio.")

# # =====================
# # Main
# # =====================
# if __name__ == "__main__":
#     print("Starting real-time transcription with partials and GPT-4 translation...")

#     # Start capturing audio in a separate thread
#     capture_thread = threading.Thread(target=capture_audio)
#     capture_thread.daemon = True
#     capture_thread.start()

#     time.sleep(1)

#     audio_stream = QueueStream(audio_queue)
#     try:
#         ws.run_synchronously(audio_stream, config, settings)
#     except Exception as e:
#         print(f"Error during transcription: {e}")

#     # Flush any remaining text on exit
#     if transcript_buffer:
#         persian_text = transcript_buffer.strip()
#         print(f"[Final (fa)] {persian_text}")
#         for lang in TARGET_LANGUAGES:
#             translated_text = translate_with_gpt4(persian_text, "Persian", lang)
#             print(f"[{lang}] {translated_text}")
#         transcript_buffer = ""

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\nShutting down...")



# Transcribe with Speechmatics, Translation with GPT-4:Best So Far##
####################################################################
####################################################################
####################################################################
####################################################################

# import openai
# import pyaudio
# import speechmatics
# from speechmatics.models import ConnectionSettings, TranscriptionConfig, AudioSettings, ServerMessageType
# import threading
# import queue
# import time
# import os

# # =====================
# # Configuration
# # =====================
# AUTH_TOKEN = ""  # Speechmatics
# CONNECTION_URL = "wss://eu2.rt.speechmatics.com/v2"

# SOURCE_LANGUAGE = "fa"   # Persian
# TARGET_LANGUAGES = ["en", "nl"]  # English, Dutch

# CHUNK_SIZE = 1024
# SAMPLE_RATE = 44100
# CHANNELS = 1
# FORMAT = pyaudio.paInt16
# SAMPLE_WIDTH = 2

# # Set your OpenAI API Key (preferably from an env var)
# # openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR-OPENAI-KEY")  
# # or, less securely:
# openai.api_key = ""

# # =====================
# # Globals
# # =====================
# transcript_buffer = ""
# audio_queue = queue.Queue()

# # Create Speechmatics WebSocket client
# ws = speechmatics.client.WebsocketClient(
#     ConnectionSettings(
#         url=CONNECTION_URL,
#         auth_token=AUTH_TOKEN
#     )
# )

# # =====================
# # GPT Translation Function
# # =====================
# def translate_with_gpt4(text: str, source_lang: str, target_lang: str) -> str:
#     """
#     Use OpenAI's GPT-4 to translate from source_lang to target_lang.
#     The prompt is structured to produce a direct translation.
#     """
#     try:
#         system_prompt = (
#             f"You are a helpful translation assistant. "
#             f"Please translate text from {source_lang} to {target_lang}. "
#             f"Output only the translated text without extra explanations."
#         )
        
#         # We'll put the source text in the user message.
#         user_message = f"Translate this text into {target_lang}:\n\n{text}"
        
#         response = openai.ChatCompletion.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_message}
#             ],
#             temperature=0.0,  # 0.0 is more "deterministic"
#         )
        
#         # Extract the translation text
#         translated_text = response['choices'][0]['message']['content'].strip()
#         return translated_text
#     except Exception as e:
#         return f"<GPT Translation Error: {e}>"

# # =====================
# # Final Transcript Handler
# # =====================
# def handle_final_transcript(msg):
#     global transcript_buffer
#     final_text = msg['metadata']['transcript'].strip()
#     transcript_buffer += " " + final_text
    
#     # If text ends with punctuation or is long enough, translate
#     if final_text.endswith(('.', '!', '?')) or len(transcript_buffer.split()) > 10:
#         # Print the entire buffer in Persian
#         persian_text = transcript_buffer.strip()
#         print(f"[Final (fa)] {persian_text}")
        
#         # Translate to target languages using GPT-4
#         for target_lang in TARGET_LANGUAGES:
#             translated_text = translate_with_gpt4(
#                 text=persian_text,
#                 source_lang="Persian",
#                 target_lang=target_lang
#             )
#             print(f"[{target_lang}] {translated_text}")
        
#         # Reset buffer
#         transcript_buffer = ""

# # Register the final transcript event handler
# ws.add_event_handler(
#     event_name=ServerMessageType.AddTranscript,
#     event_handler=handle_final_transcript
# )

# # =====================
# # Speechmatics Settings
# # =====================
# settings = AudioSettings(
#     encoding="pcm_s16le",
#     sample_rate=SAMPLE_RATE,
#     chunk_size=CHUNK_SIZE
# )

# config = TranscriptionConfig(
#     language=SOURCE_LANGUAGE,
#     enable_partials=False,  # or True if you want partial transcripts
#     max_delay=5,
#     operating_point="enhanced"
# )

# # =====================
# # Audio Capture / Queue
# # =====================
# class QueueStream:
#     def __init__(self, q):
#         self.queue = q
#         self.running = True

#     def read(self, num_bytes):
#         while self.running:
#             try:
#                 data = self.queue.get(timeout=2)
#                 if data is None:
#                     self.running = False
#                     return b""
#                 if len(data) > 0:
#                     return data
#             except queue.Empty:
#                 continue
#         return b""

# def capture_audio():
#     p = pyaudio.PyAudio()
#     stream = p.open(
#         format=FORMAT,
#         channels=CHANNELS,
#         rate=SAMPLE_RATE,
#         input=True,
#         frames_per_buffer=CHUNK_SIZE
#     )
#     print("Capturing audio from microphone... Speak now (in Persian)!")
#     try:
#         while True:
#             data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
#             audio_queue.put(data)
#     except KeyboardInterrupt:
#         stream.stop_stream()
#         stream.close()
#         p.terminate()
#         audio_queue.put(None)
#         print("\nStopped capturing audio.")

# # =====================
# # Main Execution
# # =====================
# if __name__ == "__main__":
#     print("Starting real-time transcription with GPT-4 translation...")

#     # Start capturing audio in a thread
#     capture_thread = threading.Thread(target=capture_audio)
#     capture_thread.daemon = True
#     capture_thread.start()

#     time.sleep(1)

#     # Create the custom audio stream and run the Speechmatics client
#     audio_stream = QueueStream(audio_queue)
#     try:
#         ws.run_synchronously(audio_stream, config, settings)
#     except Exception as e:
#         print(f"Error during transcription: {e}")

#     # Flush any remaining buffer
#     if transcript_buffer:
#         persian_text = transcript_buffer.strip()
#         print(f"[Final (fa)] {persian_text}")
        
#         for target_lang in TARGET_LANGUAGES:
#             translated_text = translate_with_gpt4(
#                 text=persian_text,
#                 source_lang="Persian",
#                 target_lang=target_lang
#             )
#             print(f"[{target_lang}] {translated_text}")
#         transcript_buffer = ""

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("\nShutting down...")
