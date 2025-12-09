"""
In-process end-to-end tests using FastAPI TestClient.
- Avoids external uvicorn lifecycle issues.
- Runs text and voice tests for en/hi/fr using existing app (backend.main.app).

Run with backend venv Python:
D:/lexi/backend/venv/Scripts/python scripts/e2e_test_client.py
"""

import sys
from pathlib import Path
import json
import base64

# Ensure project root is on sys.path so `backend` package can be imported
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app
OUTPUT_DIR = Path("scripts/e2e_outputs_client")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEST_CASES = [
    {"country": "usa", "user_language": "en", "query": "Can I work on a student visa in the USA?", "label": "English (USA)"},
    {"country": "india", "user_language": "hi", "query": "छात्र वीज़ा पर क्या मैं काम कर सकता हूँ?", "label": "Hindi (India)"},
    {"country": "canada", "user_language": "fr", "query": "Puis-je travailler avec un visa d'étudiant au Canada?", "label": "French (Canada)"}
]


def synthesize_audio_local(text, lang, out_path):
    try:
        from gtts import gTTS
    except Exception as e:
        raise RuntimeError("gTTS is required for voice tests. Install it in the backend venv: pip install gTTS")

    tts = gTTS(text=text, lang=lang)
    tts.save(str(out_path))
    return out_path


with TestClient(app) as client:
    print("Running text tests using TestClient")
    for t in TEST_CASES:
        payload = {"country": t['country'], "query": t['query'], "user_language": t['user_language'], "include_audio": False}
        print(f"\n>> Text Test: {t['label']}")
        r = client.post("/api/v1/chat/", json=payload, timeout=120)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Answer:", data.get('answer'))
            print("User language returned:", data.get('user_language'))
            out = OUTPUT_DIR / f"text_{t['user_language']}.json"
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            print("Saved response to", out)
        else:
            print("Error response:", r.text)

    print("\nRunning voice tests using TestClient")
    for t in TEST_CASES:
        print(f"\n>> Voice Test: {t['label']}")
        audio_file = OUTPUT_DIR / f"in_{t['user_language']}.mp3"
        synthesize_audio_local(t['query'], t['user_language'], audio_file)
        with open(audio_file, 'rb') as fh:
            files = {"audio_file": (audio_file.name, fh, 'audio/mpeg')}
            data = {"country": t['country'], "user_language": t['user_language'], "include_audio": "true"}
            r = client.post("/api/v1/chat/voice", files=files, data=data, timeout=180)
            print("Status:", r.status_code)
            if r.status_code == 200:
                resp = r.json()
                print("Transcribed (snippet):", resp.get('reasoning','')[:200])
                print("Answer:", resp.get('answer'))
                out = OUTPUT_DIR / f"voice_{t['user_language']}.json"
                out.write_text(json.dumps(resp, ensure_ascii=False, indent=2), encoding='utf-8')
                if resp.get('audio_base64'):
                    audio_bytes = base64.b64decode(resp['audio_base64'])
                    audio_out = OUTPUT_DIR / f"out_{t['user_language']}.{resp.get('audio_format','mp3')}"
                    audio_out.write_bytes(audio_bytes)
                    print("Saved returned audio to", audio_out)
            else:
                print("Error:", r.text)

    print("\nTestClient E2E runs complete. Outputs in:", OUTPUT_DIR)
