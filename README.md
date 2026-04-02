# tts-podcast

Generate podcast-quality audio from text scripts using **Google Chirp 3 HD voices** via the Cloud Text-to-Speech API.

---

## Prerequisites

1. **Google Cloud project** with the Cloud Text-to-Speech API enabled.
2. **gcloud CLI** installed and authenticated:
   ```bash
   gcloud auth application-default login
   ```
3. **Python 3.11+**

---

## Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your project
cp .env.example .env
# Edit .env — set GCP_PROJECT_ID to your Google Cloud project ID
```

---

## Generate Audio

```bash
# Basic usage — outputs to output/episode1.mp3
python scripts/synthesize.py --input-file scripts/episode1.txt

# Custom output path
python scripts/synthesize.py \
  --input-file scripts/episode1.txt \
  --output output/my_episode.mp3

# Different voice (see voices below)
python scripts/synthesize.py \
  --input-file scripts/episode1.txt \
  --voice en-US-Chirp3-HD-Charon
```

---

## Available Chirp 3 HD Voices

| Voice name | Character |
|---|---|
| `en-US-Chirp3-HD-Zephyr` | Warm, conversational *(default)* |
| `en-US-Chirp3-HD-Charon` | Deep, authoritative |
| `en-US-Chirp3-HD-Kore` | Bright, energetic |
| `en-US-Chirp3-HD-Aoede` | Smooth, storytelling |
| `en-US-Chirp3-HD-Puck` | Playful, upbeat |
| `en-US-Chirp3-HD-Fenrir` | Bold, grounded |
| `en-US-Chirp3-HD-Leda` | Clear, professional |
| `en-US-Chirp3-HD-Orus` | Calm, measured |

---

## Project Layout

```
tts-podcast/
├── scripts/
│   ├── synthesize.py      # main TTS script
│   └── episode1.txt       # sample podcast script
├── output/                # generated MP3s (git-ignored)
├── .env.example           # config template
├── requirements.txt
└── README.md
```

---

## Coming Soon

- `generate_voice_key.py` — clone your own voice with ~10s of reference audio (requires Google Cloud allow-list access for Instant Custom Voice)
