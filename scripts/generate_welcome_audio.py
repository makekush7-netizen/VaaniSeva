# VaaniSeva - Generate & Upload Welcome Audio
# Generates separate TTS clips per language using Sarvam AI and uploads to S3.
# The Lambda plays them sequentially inside <Gather> — no audio stitching needed.
#
# Run: python scripts/generate_welcome_audio.py

import os, base64, uuid, boto3, requests
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.environ["SARVAM_API_KEY"]
S3_BUCKET      = os.environ["S3_DOCUMENTS_BUCKET"]
AWS_REGION     = os.environ["AWS_REGION"]

s3 = boto3.client("s3", region_name=AWS_REGION)

# ── Clips to generate ────────────────────────────────────────
# key → (text, sarvam_lang_code, sarvam_speaker, s3_key)
CLIPS = {
    "welcome_intro": (
        "नमस्कार! वाणीसेवा में आपका स्वागत है। "
        "मैं आपकी दीदी हूँ — सरकारी योजनाएँ हों, खेती का सवाल हो, या कुछ भी जानना हो, बस बोलिए!",
        "hi-IN", "anushka", "static-audio/welcome_intro.wav"
    ),
    "welcome_hi": (
        "हिंदी के लिए एक दबाइए।",
        "hi-IN", "anushka", "static-audio/welcome_hi.wav"
    ),
    "welcome_mr": (
        "मराठीसाठी दोन दाबा.",
        "mr-IN", "manisha", "static-audio/welcome_mr.wav"
    ),
    "welcome_ta": (
        "தமிழுக்கு மூன்று அழுத்தவும்.",
        "ta-IN", "vidya", "static-audio/welcome_ta.wav"
    ),
    "welcome_en": (
        "Press four for English.",
        "en-IN", "arya", "static-audio/welcome_en.wav"
    ),
    "no_input": (
        "अरे, कुछ सुनाई नहीं दिया। कोई बात नहीं, दोबारा कॉल कर लीजिए! मैं यहीं हूँ।",
        "hi-IN", "anushka", "static-audio/no_input.wav"
    ),
}


def generate_and_upload(label, text, lang_code, speaker, s3_key):
    print(f"\n[{label}] Generating TTS...")
    print(f"  lang={lang_code}, speaker={speaker}")
    print(f"  text: {text[:60]}...")

    resp = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        json={
            "inputs": [text],
            "target_language_code": lang_code,
            "speaker": speaker,
            "model": "bulbul:v2",
            "pace": 0.95,  # slightly slower for welcome / readability
        },
        headers={"api-subscription-key": SARVAM_API_KEY},
        timeout=15,
    )
    resp.raise_for_status()

    audio_bytes = base64.b64decode(resp.json()["audios"][0])
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=audio_bytes,
        ContentType="audio/wav",
    )
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": s3_key},
        ExpiresIn=3600,
    )
    print(f"  ✅ Uploaded → s3://{S3_BUCKET}/{s3_key}")
    return url


def main():
    print("=" * 55)
    print("VaaniSeva — Welcome Audio Generator")
    print("=" * 55)
    print(f"Bucket : {S3_BUCKET}")
    print(f"Region : {AWS_REGION}")

    for label, (text, lang, speaker, key) in CLIPS.items():
        try:
            generate_and_upload(label, text, lang, speaker, key)
        except Exception as e:
            print(f"  ❌ FAILED for {label}: {e}")

    print("\n" + "=" * 55)
    print("Done! S3 keys created:")
    for _, (_, _, _, key) in CLIPS.items():
        print(f"  static-audio/{key.split('/')[-1]}")
    print("\nThe Lambda will now play each clip sequentially in its")
    print("native voice: Intro (Hindi) → 1 Hindi → 2 Marathi → 3 Tamil → 4 English")
    print("=" * 55)


if __name__ == "__main__":
    main()
