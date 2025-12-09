"""
Test voice endpoint with a language hint mismatch: audio is Hindi but user_language is English.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from pathlib import Path
import json

INPUT = Path('scripts/e2e_outputs_client/in_hi.mp3')
OUTPUT = Path('scripts/e2e_outputs_client/mismatch_out_hi.json')

with TestClient(app) as client:
    files = {'audio_file': (INPUT.name, open(INPUT, 'rb'), 'audio/mpeg')}
    data = {'country': 'india', 'user_language': 'en', 'include_audio': 'true'}
    r = client.post('/api/v1/chat/voice', files=files, data=data, timeout=180)
    print('Status:', r.status_code)
    # Print a few helpful fields
    if r.status_code == 200:
        j = r.json()
        print('Transcribed:', j.get('reasoning', '')[:200])
        print('Answer:', j.get('answer'))
        OUTPUT.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')
    else:
        print('Response:', r.text)
        OUTPUT.write_text(r.text, encoding='utf-8')
