"""
End-to-end smoke tests for LexiVoice chat endpoints.
- Tests text chat for en/hi/fr
- Synthesizes audio (gTTS) for voice tests and posts to /api/v1/chat/voice

Run with the backend venv Python (project root):
D:\lexi\backend\venv\Scripts\python scripts/e2e_tests.py
"""

import time
import base64
import requests
import os
from pathlib import Path

BASE_URL = os.environ.get("LEXI_BASE_URL", "http://127.0.0.1:8000/api/v1")
TEXT_ENDPOINT = f"{BASE_URL}/chat/"
VOICE_ENDPOINT = f"{BASE_URL}/chat/voice"

TEST_CASES = [
    {
        "country": "usa",
        "user_language": "en",
        "query": "Can I work on a student visa in the USA?",
        "label": "English (USA)"
    },
    {
        "country": "india",
        "user_language": "hi",
        "query": "छात्र वीज़ा पर क्या मैं काम कर सकता हूँ?",
        "label": "Hindi (India)"
    },
    {
        "country": "canada",
        "user_language": "fr",
        "query": "Puis-je travailler avec un visa d'étudiant au Canada?",
        "label": "French (Canada)"
    }
]

OUTPUT_DIR = Path("scripts/e2e_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_server(timeout=60):
    deadline = time.time() + timeout
    url = f"{BASE_URL}/chat/health"
    print(f"Waiting for server at {url}...")
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                print("Server is up.")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("Timed out waiting for server.")
    return False


def run_text_tests():
    print("\n=== Running text tests ===")
    for t in TEST_CASES:
        payload = {
            "country": t["country"],
            "query": t["query"],
            "user_language": t["user_language"],
            "include_audio": False
        }
        print(f"\n>> Test: {t['label']}")
        try:
            r = requests.post(TEXT_ENDPOINT, json=payload, timeout=60)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print("Answer:", data.get("answer"))
                print("User Language returned:", data.get("user_language"))
                print("Sources:", [s.get('title') for s in data.get('sources', [])])
                # Save full response
                out_file = OUTPUT_DIR / f"text_{t['user_language']}.json"
                out_file.write_text(r.text, encoding='utf-8')
                print(f"Saved response to {out_file}")
            else:
                print("Response:", r.text)
        except Exception as e:
            print("Request failed:", e)


def synthesize_audio(text, lang, out_path):
    # Use gTTS to synthesize a small test audio for the voice endpoint
    try:
        from gtts import gTTS
    except Exception as e:
        raise RuntimeError("gTTS is required for voice tests. Install it in the backend venv.")

    tts = gTTS(text=text, lang=lang)
    tts.save(str(out_path))
    return out_path


def run_voice_tests():
    print("\n=== Running voice tests ===")
    for t in TEST_CASES:
        print(f"\n>> Voice Test: {t['label']}")
        # Create a short audio from the query text (use user_language)
        try:
            audio_file = OUTPUT_DIR / f"voice_in_{t['user_language']}.mp3"
            synthesize_audio(t['query'], t['user_language'], audio_file)
            files = {"audio_file": (audio_file.name, open(audio_file, "rb"), "audio/mpeg")}
            data = {
                "country": t['country'],
                "user_language": t['user_language'],
                "include_audio": "true"
            }
            r = requests.post(VOICE_ENDPOINT, files=files, data=data, timeout=120)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                resp = r.json()
                print("Transcribed Reasoning (snippet):", resp.get('reasoning', '')[:200])
                print("Answer (translated):", resp.get('answer'))
                print("Audio returned:", bool(resp.get('audio_base64')))
                # Save response
                out_file = OUTPUT_DIR / f"voice_response_{t['user_language']}.json"
                out_file.write_text(r.text, encoding='utf-8')
                # Save returned audio if present
                if resp.get('audio_base64'):
                    audio_b64 = resp['audio_base64']
                    audio_bytes = base64.b64decode(audio_b64)
                    audio_out = OUTPUT_DIR / f"voice_out_{t['user_language']}.{resp.get('audio_format','mp3')}"
                    audio_out.write_bytes(audio_bytes)
                    print(f"Saved returned audio to {audio_out}")
                else:
                    print("No audio returned by the server.")
            else:
                print("Server response:", r.text)
        except Exception as e:
            print("Voice test failed:", e)


if __name__ == '__main__':
    ok = wait_for_server(timeout=60)
    if not ok:
        print("Server not available. Exiting.")
        raise SystemExit(1)

    run_text_tests()
    run_voice_tests()

    print("\nE2E tests complete. Outputs in:", OUTPUT_DIR)
