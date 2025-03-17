# Live Transcription & Translation System

A real-time transcription and translation system using Speechmatics for transcription and GPT-4 for translation. The system supports Persian to English and Dutch translation.

## Prerequisites

- Python 3.7+
- Speechmatics API key
- OpenAI API key
- Working microphone

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd speechmatics
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
   - Get a Speechmatics API key from [Speechmatics](https://speechmatics.com)
   - Get an OpenAI API key from [OpenAI](https://openai.com)

4. Update the API keys in `realtime_speechmatics_GPT.py`:
```python
SPEECHMATICS_AUTH_TOKEN = "your-speechmatics-key"
openai.api_key = "your-openai-key"
```

## Usage

1. Start the transcription service:
```bash
python realtime_speechmatics_GPT.py
```
This will:
- Start listening to your microphone
- Transcribe Persian speech
- Translate to English and Dutch
- Save results to `data/transcriptions.csv`

2. Start the JSON server for vMix:
```bash
python run.py
```
This will:
- Start a Flask server on `http://localhost:5000`
- Provide JSON output at `/api/transcriptions`

3. In vMix:
- Add a Web Input or Browser Source
- Set the URL to: `http://localhost:5000/api/transcriptions`
- The endpoint will return JSON in the format:
```json
{
    "message": {
        "original_text": "Persian text",
        "en_translation": "English translation",
        "nl_translation": "Dutch translation"
    }
}
```

## Project Structure

```
speechmatics/
├── data/                  # Directory for CSV files (created automatically)
├── app/
│   ├── models/           # Data model for CSV operations
│   └── views/            # Flask routes
├── realtime_speechmatics_GPT.py  # Main transcription script
├── run.py                # Flask server for JSON output
└── requirements.txt      # Python dependencies
```

## Notes

- The system requires a working microphone
- Speak in Persian for transcription
- The CSV file is created automatically in the `data` directory. Transcriptions are stored in a CSV file (`transcriptions.csv`) with the 
following columns:
  - timestamp: When the transcription was created
  - original_text: The Persian text
  - en_translation: English translation
  - nl_translation: Dutch translation
  - read: Boolean indicating if the transcription has been read
- Each transcription is marked as read after being fetched by vMix 