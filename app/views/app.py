from flask import Flask, jsonify
from ..models.transcription_model import TranscriptionModel

app = Flask(__name__)
model = TranscriptionModel()

@app.route('/api/transcriptions', methods=['GET'])
def get_transcriptions():
    # Get only the next unread transcription
    transcription = model.get_next_unread_transcription()
    if transcription:
        # Create the JSON structure
        json_data = {
            "message": {
                "original_text": transcription['original_text'],
                "en_translation": transcription['en_translation'],
                "nl_translation": transcription['nl_translation']
            }
        }
        # Mark it as read before returning
        model.mark_as_read(transcription['timestamp'])
        return jsonify(json_data)
    return jsonify({"message": None}) 