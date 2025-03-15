# Real-time Speech Transcription and Translation

A Python application that performs real-time speech transcription using Speechmatics API and translation using GPT-4.

## Features

- Real-time speech transcription in Persian (fa)
- Translation to multiple languages (English, Dutch)
- Low-latency processing
- High accuracy transcription using Speechmatics
- Neural machine translation using GPT-4

## Requirements

- Python 3.9+
- PyAudio
- Speechmatics API access
- OpenAI API access

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
export SPEECHMATICS_AUTH_TOKEN="your_speechmatics_token"
export OPENAI_API_KEY="your_openai_key"
```

You can also create a `.env` file:
```bash
SPEECHMATICS_AUTH_TOKEN=your_speechmatics_token
OPENAI_API_KEY=your_openai_key
```

## Usage

Run the script:
```bash
python realtime_speechmatics_GPT.py
```

## Configuration

- Source language: Persian (fa)
- Target languages: English (en), Dutch (nl)
- Audio settings: 16kHz, 16-bit, mono

## Security Note

Never commit your API keys to the repository. Always use environment variables or a `.env` file (and make sure to add `.env` to your `.gitignore`). 