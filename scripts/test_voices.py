"""
test_voices.py — Listen to all Sarvam AI voices
Usage: python scripts/test_voices.py
"""
import os, sys, base64, tempfile, subprocess, time
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
if not SARVAM_API_KEY:
    print("ERROR: SARVAM_API_KEY not found in .env")
    sys.exit(1)

# All Sarvam AI bulbul:v2 speakers — verified list from API
VOICES = [
    # (speaker, lang_code, language_label, sample_text)
    ("anushka",  "hi-IN", "Hindi",            "नमस्ते! मैं वाणीसेवा हूँ। मेरा नाम अनुष्का है।"),
    ("abhilash", "hi-IN", "Hindi",            "नमस्ते! मैं वाणीसेवा हूँ। मेरा नाम अभिलाश है।"),
    ("manisha",  "mr-IN", "Marathi",          "नमस्कार! मी वाणीसेवा आहे. माझे नाव मनिषा आहे."),
    ("vidya",    "en-IN", "English (Indian)", "Hello! I am VaaniSeva. My name is Vidya."),
    ("arya",     "hi-IN", "Hindi",            "नमस्ते! मैं वाणीसेवा हूँ। मेरा नाम आर्या है।"),
    ("karun",    "hi-IN", "Hindi",            "नमस्ते! मैं वाणीसेवा हूँ। मेरा नाम करुण है।"),
    ("hitesh",   "hi-IN", "Hindi",            "नमस्ते! मैं वाणीसेवा हूँ। मेरा नाम हितेश है।"),
]

def play_audio(wav_bytes: bytes, label: str):
    """Write wav to temp file and play via Windows Media Player."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp = f.name
    print(f"  ▶  Playing {label}...")
    subprocess.run(
        ["powershell", "-c", f'(New-Object Media.SoundPlayer "{tmp}").PlaySync()'],
        check=False, capture_output=True
    )
    os.unlink(tmp)

def test_voice(speaker: str, lang_code: str, language: str, text: str) -> bool:
    print(f"\n{'─'*55}")
    print(f"  Speaker : {speaker}")
    print(f"  Language: {language} ({lang_code})")
    print(f"  Text    : {text}")
    try:
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            json={
                "inputs": [text],
                "target_language_code": lang_code,
                "speaker": speaker,
                "model": "bulbul:v2",
                "enable_preprocessing": True,
            },
            headers={"api-subscription-key": SARVAM_API_KEY},
            timeout=15,
        )
        if r.status_code != 200:
            print(f"  ✗  HTTP {r.status_code}: {r.text[:120]}")
            return False

        data = r.json()
        audios = data.get("audios", [])
        if not audios:
            print(f"  ✗  No audio in response")
            return False

        wav_bytes = base64.b64decode(audios[0])
        play_audio(wav_bytes, f"{speaker} ({language})")
        print(f"  ✓  Done")
        return True

    except Exception as e:
        print(f"  ✗  Error: {e}")
        return False

def main():
    print("=" * 55)
    print("  Sarvam AI — Voice Preview (bulbul:v2)")
    print("=" * 55)
    print(f"  Total voices to test: {len(VOICES)}")
    print(f"  Press Ctrl+C at any time to stop.\n")

    passed, failed = 0, []

    for speaker, lang_code, language, text in VOICES:
        ok = test_voice(speaker, lang_code, language, text)
        if ok:
            passed += 1
        else:
            failed.append(speaker)
        time.sleep(0.5)  # brief pause between voices

    print(f"\n{'='*55}")
    print(f"  Results: {passed}/{len(VOICES)} voices played successfully")
    if failed:
        print(f"  Failed / unavailable: {', '.join(failed)}")
    print("=" * 55)

if __name__ == "__main__":
    main()
