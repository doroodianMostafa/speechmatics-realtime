import speechmatics
from speechmatics.models import (
    ConnectionSettings,
    TranscriptionConfig,
    AudioSettings,
    ServerMessageType
)
import pyaudio
import threading
import queue
import time
from ..models.transcription_model import TranscriptionModel
from ..models.translation_model import TranslationModel
from ..config import Config

class TranscriptionController:
    def __init__(self):
        self.model = TranscriptionModel()
        self.translation_model = TranslationModel()
        self.audio_queue = queue.Queue()
        self.transcript_buffer = ""
        self.print_lock = threading.Lock()
        self.running = False
        self.audio_thread = None
        self.transcription_thread = None
        
        # Validate configuration
        Config.validate()
        
        # Initialize Speechmatics client
        self._init_speechmatics()
        
        # Initialize audio capture
        self._init_audio()

    def _init_speechmatics(self):
        """Initialize Speechmatics client"""
        try:
            self.ws = speechmatics.client.WebsocketClient(
                ConnectionSettings(
                    url=Config.SPEECHMATICS_URL,
                    auth_token=Config.SPEECHMATICS_AUTH_TOKEN
                )
            )
            
            # Register event handler
            self.ws.add_event_handler(
                event_name=ServerMessageType.AddTranscript,
                event_handler=self.handle_final_transcript
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Speechmatics client: {e}")

    def _init_audio(self):
        """Initialize audio capture"""
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=Config.CHANNELS,
                rate=Config.SAMPLE_RATE,
                input=True,
                frames_per_buffer=Config.CHUNK_SIZE
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize audio capture: {e}")

    def start(self):
        """Start the transcription and translation process"""
        if self.running:
            return

        self.running = True
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(target=self._capture_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()

        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self._start_transcription)
        self.transcription_thread.daemon = True
        self.transcription_thread.start()

        print("Transcription system started. Speak in Persian...")

    def stop(self):
        """Stop the transcription and translation process"""
        if not self.running:
            return

        self.running = False
        self.audio_queue.put(None)  # Signal audio thread to stop

        # Wait for threads to finish
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        if self.transcription_thread:
            self.transcription_thread.join(timeout=2)

        # Cleanup resources
        if hasattr(self, 'stream'):
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'p'):
            self.p.terminate()

        print("Transcription system stopped.")

    def _capture_audio(self):
        """Capture audio from microphone"""
        try:
            while self.running:
                try:
                    data = self.stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)
                    self.audio_queue.put(data)
                except IOError as e:
                    print(f"Audio capture error: {e}")
                    time.sleep(0.1)  # Brief pause before retrying
        except Exception as e:
            print(f"Fatal audio capture error: {e}")
        finally:
            self.audio_queue.put(None)  # Signal transcription thread to stop

    def _start_transcription(self):
        """Start the Speechmatics transcription process"""
        settings = AudioSettings(
            encoding=Config.FORMAT,
            sample_rate=Config.SAMPLE_RATE,
            chunk_size=Config.CHUNK_SIZE
        )

        config = TranscriptionConfig(
            language=Config.SOURCE_LANGUAGE,
            enable_partials=False,
            max_delay=2.5,
            operating_point="enhanced"
        )

        try:
            self.ws.run_synchronously(QueueStream(self.audio_queue), config, settings)
        except Exception as e:
            print(f"Transcription error: {e}")

    def handle_final_transcript(self, msg):
        final_text = msg['metadata']['transcript'].strip()
        self.transcript_buffer += " " + final_text
        
        if final_text.endswith(('.', '!', '?')) or len(self.transcript_buffer.split()) >= 10:
            persian_text = self.transcript_buffer.strip()
            self.transcript_buffer = ""
            
            with self.print_lock:
                print(f"\n[Original] {persian_text}")

            def process_translation():
                translations = self.translation_model.translate(persian_text)
                self.model.save_transcription(persian_text, translations)
                
                with self.print_lock:
                    for lang in Config.TARGET_LANGUAGES:
                        print(f"[{lang.upper()}] {translations.get(lang, '')}")
                    print("\n")
            
            threading.Thread(target=process_translation).start()

    def get_all_transcriptions(self):
        return self.model.get_all_transcriptions()

    def get_next_unread_transcription(self):
        """Get the next unread transcription"""
        return self.model.get_next_unread_transcription()

    def mark_as_read(self, timestamp):
        self.model.mark_as_read(timestamp)

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