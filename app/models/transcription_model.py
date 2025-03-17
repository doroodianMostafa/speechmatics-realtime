import csv
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TranscriptionModel:
    def __init__(self, csv_file='data/transcriptions.csv'):
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        self.csv_file = csv_file
        logger.debug(f"Initializing TranscriptionModel with CSV file: {csv_file}")
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        if not os.path.exists(self.csv_file):
            logger.debug(f"Creating new CSV file: {self.csv_file}")
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'original_text', 'en_translation', 'nl_translation', 'read'])
        else:
            logger.debug(f"CSV file already exists: {self.csv_file}")

    def save_transcription(self, original_text, translations):
        logger.debug(f"Saving transcription: {original_text}")
        logger.debug(f"Translations: {translations}")
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                row = [
                    datetime.now().isoformat(),
                    original_text,
                    translations.get('en', ''),
                    translations.get('nl', ''),
                    'false'
                ]
                writer.writerow(row)
                logger.debug(f"Successfully saved row: {row}")
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")
            raise

    def get_all_transcriptions(self):
        logger.debug(f"Reading all transcriptions from: {self.csv_file}")
        transcriptions = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    transcriptions.append(row)
            logger.debug(f"Found {len(transcriptions)} transcriptions")
            return transcriptions
        except Exception as e:
            logger.error(f"Error reading transcriptions: {e}")
            raise

    def get_next_unread_transcription(self):
        """Get the next unread transcription in chronological order"""
        logger.debug("Getting next unread transcription")
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['read'] == 'false':
                        logger.debug(f"Found next unread transcription: {row}")
                        return row
            logger.debug("No unread transcriptions found")
            return None
        except Exception as e:
            logger.error(f"Error getting next unread transcription: {e}")
            raise

    def mark_as_read(self, timestamp):
        logger.debug(f"Marking transcription as read: {timestamp}")
        rows = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['timestamp'] == timestamp:
                        row['read'] = 'true'
                        logger.debug(f"Found and marked row: {row}")
                    rows.append(row)

            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            logger.debug("Successfully updated CSV file")
        except Exception as e:
            logger.error(f"Error marking transcription as read: {e}")
            raise 