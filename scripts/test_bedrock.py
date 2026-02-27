# VaaniSeva - Test Bedrock connectivity
# Run: python scripts/test_bedrock.py
# Confirms Claude 3.5 Sonnet + Titan Embeddings are working with your AWS keys

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])

def test_claude():
    print("\n🔍 Testing Claude 3.5 Sonnet...")
    try:
        response = bedrock.invoke_model(
            modelId=os.environ["BEDROCK_MODEL_ID"],
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.3,
                "messages": [{
                    "role": "user",
                    "content": "Say exactly: VaaniSeva Claude test passed."
                }]
            }),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        text = result["content"][0]["text"]
        print(f"  ✅ Claude response: {text}")
        return True
    except Exception as e:
        print(f"  ❌ Claude FAILED: {e}")
        return False


def test_embeddings():
    print("\n🔍 Testing Titan Embeddings v2...")
    try:
        response = bedrock.invoke_model(
            modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
            body=json.dumps({"inputText": "PM Kisan yojana kya hai"}),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read())
        embedding = result["embedding"]
        print(f"  ✅ Embedding generated — dimensions: {len(embedding)}")
        return True
    except Exception as e:
        print(f"  ❌ Embeddings FAILED: {e}")
        return False


def test_sarvam():
    api_key = os.environ.get("SARVAM_API_KEY", "")
    print("\n🔍 Testing Sarvam AI TTS...")
    if not api_key or api_key == "your_sarvam_api_key_here":
        print("  ⏭️  Skipped — SARVAM_API_KEY not set yet")
        return None
    try:
        import requests
        resp = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            json={
                "inputs": ["Namaste, VaaniSeva test chal raha hai."],
                "target_language_code": "hi-IN",
                "speaker": "anushka",
                "model": "bulbul:v2"
            },
            headers={"api-subscription-key": api_key},
            timeout=10
        )
        resp.raise_for_status()
        audio_len = len(resp.json().get("audios", [""])[0])
        print(f"  ✅ Sarvam TTS OK — audio base64 length: {audio_len} chars")
        return True
    except Exception as e:
        print(f"  ❌ Sarvam TTS FAILED: {e}")
        return False


if __name__ == "__main__":
    print("=" * 45)
    print("VaaniSeva - Bedrock + Services Test")
    print("=" * 45)

    claude_ok     = test_claude()
    embedding_ok  = test_embeddings()
    sarvam_result = test_sarvam()

    print("\n" + "=" * 45)
    print("SUMMARY")
    print("=" * 45)
    print(f"  Claude 3.5 Sonnet  : {'✅ OK' if claude_ok else '❌ FAILED'}")
    print(f"  Titan Embeddings   : {'✅ OK' if embedding_ok else '❌ FAILED'}")
    if sarvam_result is None:
        print(f"  Sarvam AI TTS      : ⏭️  Not tested (add key)")
    else:
        print(f"  Sarvam AI TTS      : {'✅ OK' if sarvam_result else '❌ FAILED'}")

    if claude_ok and embedding_ok:
        print("\n✅ All core services working. Ready to deploy!")
    else:
        print("\n❌ Fix failing services before deploying.")
