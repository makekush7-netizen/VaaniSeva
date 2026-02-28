# VaaniSeva - Lambda: call-handler
# TTS: Sarvam AI (primary, better Hindi) → Amazon Polly via Twilio builtin (fallback)
# STT: Twilio native Gather speech recognition (free, built-in)
# LLM: Amazon Bedrock Nova Micro (Amazon native, no card required) + RAG

import json
import os
import base64
import math
import uuid
import logging
import boto3
import requests
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients ──────────────────────────────────────────────
dynamodb  = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock   = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
s3_client = boto3.client("s3", region_name=os.environ["AWS_REGION"])

calls_table     = dynamodb.Table(os.environ["DYNAMODB_CALLS_TABLE"])
knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── Config ───────────────────────────────────────────────────
BEDROCK_MODEL_ID           = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_EMBEDDING_MODEL_ID = os.environ["BEDROCK_EMBEDDING_MODEL_ID"]
SARVAM_API_KEY             = os.environ.get("SARVAM_API_KEY", "")
S3_BUCKET                  = os.environ["S3_DOCUMENTS_BUCKET"]
BASE_URL                   = ""  # Set at runtime from API Gateway event

SYSTEM_PROMPT = """You are VaaniSeva (वाणीसेवा), an AI phone assistant helping rural Indians learn about government schemes.

RULES:
- When the user speaks Hindi, you MUST reply in pure Devanagari Hindi (हिंदी). NEVER use romanized/Hinglish like "aap" or "yojana". Always write आप, योजना, etc.
- When the user speaks English, reply in simple English.
- Use simple, everyday words a villager would understand — no jargon.
- Keep answers to 2-3 short sentences max (this is a phone call, not an essay).
- You know about: PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas Yojana, Sukanya Samriddhi, PM Mudra, PM Fasal Bima, Atal Pension, PM SVANidhi, Beti Bachao, Janani Suraksha, PM Garib Kalyan Anna, Jan Dhan, PM Ujjwala, National Scholarship Portal.
- If asked about something else, say you only know about government schemes.
- End with asking if they want to know more."""


# ══════════════════════════════════════════════════════════════
#  TTS: Sarvam AI → Amazon Polly fallback
# ══════════════════════════════════════════════════════════════

def sarvam_tts(text: str, language: str) -> str | None:
    """
    Call Sarvam AI TTS. Uploads audio to S3, returns presigned URL (1hr).
    Returns None on any failure so caller can fall back to Polly.
    """
    if not SARVAM_API_KEY:
        return None
    try:
        payload = {
            "inputs": [text],
            "target_language_code": "hi-IN" if language == "hi" else "en-IN",
            "speaker": "anushka" if language == "hi" else "vidya",
            "model": "bulbul:v2"
        }
        resp = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            json=payload,
            headers={"api-subscription-key": SARVAM_API_KEY},
            timeout=8
        )
        resp.raise_for_status()
        audio_bytes = base64.b64decode(resp.json()["audios"][0])
        key = f"tts/{uuid.uuid4()}.wav"
        s3_client.put_object(Bucket=S3_BUCKET, Key=key, Body=audio_bytes, ContentType="audio/wav")
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=3600
        )
        logger.info(f"Sarvam TTS OK → {key}")
        return url
    except Exception as e:
        logger.warning(f"Sarvam TTS failed, falling back to Polly: {e}")
        return None


def tts_say(target, text: str, language: str):
    """
    Add TTS audio to a TwiML Gather or Response object.
    Tries Sarvam AI first; falls back to Amazon Polly via Twilio builtin <Say>.
    """
    audio_url = sarvam_tts(text, language)
    if audio_url:
        target.play(audio_url)   # Sarvam audio from S3
    else:
        voice = "Polly.Aditi" if language == "hi" else "Polly.Raveena"
        target.say(text, voice=voice)  # Polly via Twilio — zero extra config


# ── Main Lambda handler ──────────────────────────────────────
def lambda_handler(event, context):
    global BASE_URL
    logger.info(f"Event: {json.dumps(event)}")

    # ── Amazon Connect event? (has "Details" key) ────────────
    if "Details" in event:
        from connect_handler import handle_connect_event
        return handle_connect_event(event)

    # ── Otherwise: Twilio via API Gateway ────────────────────
    # API Gateway wraps the body as a string
    body = event.get("body", "")
    if isinstance(body, str):
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body).items()}
    else:
        params = body or {}

    # Build absolute base URL so Twilio follows redirects through API Gateway stage
    req_ctx = event.get("requestContext", {})
    domain = req_ctx.get("domainName", "")
    stage  = req_ctx.get("stage", "prod")
    BASE_URL = f"https://{domain}/{stage}" if domain else ""

    path = event.get("path", "/voice/incoming")

    if "/incoming" in path:
        return handle_incoming(params)
    elif "/language" in path:
        return handle_language_select(params)
    elif "/gather" in path:
        return handle_gather(params)
    else:
        return twiml_response(VoiceResponse())


# ── Step 1: New call comes in ────────────────────────────────
def handle_incoming(params):
    call_sid = params.get("CallSid", str(uuid.uuid4()))
    from_number = params.get("From", "unknown")

    # Save call to DynamoDB
    calls_table.put_item(Item={
        "call_id": call_sid,
        "timestamp": int(datetime.now().timestamp()),
        "from_number": from_number,
        "status": "in-progress",
        "language": "en",  # default, user will select
        "queries_count": 0,
        "conversation_history": []
    })

    response = VoiceResponse()
    action_url = f"{BASE_URL}/voice/language" if BASE_URL else "/voice/language"
    gather = Gather(num_digits=1, action=action_url, method="POST", timeout=10)

    # Pre-recorded Sarvam TTS welcome audio from S3
    welcome_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": "static-audio/welcome_combined.wav"},
        ExpiresIn=3600,
    )
    gather.play(welcome_url)
    response.append(gather)

    # Pre-recorded Sarvam TTS no-input fallback from S3
    no_input_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": "static-audio/no_input.wav"},
        ExpiresIn=3600,
    )
    response.play(no_input_url)

    return twiml_response(response)


# ── Step 2: Language selected ────────────────────────────────
def handle_language_select(params):
    call_sid = params.get("CallSid", "")
    digit    = params.get("Digits", "2")
    language = "hi" if digit == "1" else "en"

    # Update language in DynamoDB
    calls_table.update_item(
        Key={"call_id": call_sid, "timestamp": get_call_timestamp(call_sid)},
        UpdateExpression="SET #lang = :lang",
        ExpressionAttributeNames={"#lang": "language"},
        ExpressionAttributeValues={":lang": language}
    )

    prompt = (
        "आप कौनसी सरकारी योजना के बारे में जानना चाहते हैं? बोलिए।"
        if language == "hi"
        else "Which government scheme would you like to know about? Please speak."
    )
    fallback_msg = (
        "कुछ सुनाई नहीं दिया। कृपया दोबारा कॉल करें।"
        if language == "hi" else "I didn't hear anything. Please call again."
    )

    response = VoiceResponse()
    gather_url = f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}"
    gather = Gather(
        input="speech",
        action=gather_url,
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=10
    )
    tts_say(gather, prompt, language)
    response.append(gather)
    tts_say(response, fallback_msg, language)
    return twiml_response(response)


# ── Step 3: User spoke — process query ──────────────────────
def handle_gather(params):
    call_sid    = params.get("CallSid", "")
    speech_text = params.get("SpeechResult", "")
    language    = params.get("lang", "en")

    logger.info(f"Speech: '{speech_text}' | Lang: {language} | Call: {call_sid}")

    if not speech_text:
        return ask_again(language)

    try:
        answer = rag_pipeline(speech_text, language)
    except Exception as e:
        logger.error(f"RAG error: {e}")
        answer = (
            "मुझे अभी कुछ तकलीफ हो रही है। थोड़ी देर बाद कोशिश करें।"
            if language == "hi"
            else "I'm having trouble right now. Please try again in a moment."
        )

    follow_up = (
        "क्या आप और कुछ जानना चाहते हैं?"
        if language == "hi" else "Would you like to know anything else?"
    )
    goodbye = "धन्यवाद। वाणीसेवा में कॉल करने के लिए शुक्रिया।" if language == "hi" \
              else "Thank you for calling VaaniSeva. Goodbye."

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}",
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=15
    )
    tts_say(gather, f"{answer} {follow_up}", language)
    response.append(gather)
    tts_say(response, goodbye, language)

    log_query(call_sid, speech_text, answer, language)
    return twiml_response(response)


# ── RAG Pipeline ─────────────────────────────────────────────
def rag_pipeline(query: str, language: str) -> str:
    embedding = get_embedding(query)
    context   = retrieve_context(embedding, language)
    return ask_llm(query, context, language)


def get_embedding(text: str) -> list:
    response = bedrock.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def cosine_similarity(a: list, b: list) -> float:
    # Convert Decimal to float (DynamoDB stores as Decimal)
    a = [float(x) for x in a]
    b = [float(x) for x in b]
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b + 1e-9)


def retrieve_context(query_embedding: list, language: str) -> str:
    """Cosine similarity search against vaaniseva-vectors table (scan OK for small dataset)."""
    items = vectors_table.scan().get("Items", [])
    if not items:
        return "No scheme information loaded yet."

    scored = [
        (cosine_similarity(query_embedding, item.get("embedding", [])), item)
        for item in items if item.get("embedding")
    ]
    top      = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
    lang_key = "hi" if language == "hi" else "en"
    return "\n\n".join(item.get(f"text_{lang_key}", item.get("text", "")) for _, item in top)


def ask_llm(query: str, context: str, language: str) -> str:
    lang_instruction = "जवाब पूरी तरह हिंदी देवनागरी लिपि में दो। कोई भी अंग्रेजी या रोमन अक्षर मत लिखो।" if language == "hi" else "Respond in simple English."

    user_msg = f"""{lang_instruction}

Context from government scheme database:
{context}

User's question: {query}

Answer in 2-3 short sentences suitable for a phone call."""

    messages = [
        {"role": "user", "content": [{"text": f"{SYSTEM_PROMPT}\n\n{user_msg}"}]}
    ]

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps({
            "messages": messages,
            "inferenceConfig": {
                "max_new_tokens": 300,
                "temperature": 0.3
            }
        }),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()


# ── Helpers ──────────────────────────────────────────────────
def ask_again(language: str):
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}",
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=10
    )
    msg = "कृपया दोबारा बोलिए।" if language == "hi" else "Sorry, please say that again."
    tts_say(gather, msg, language)
    response.append(gather)
    return twiml_response(response)


def log_query(call_sid: str, query: str, answer: str, language: str):
    try:
        timestamp = get_call_timestamp(call_sid)
        calls_table.update_item(
            Key={"call_id": call_sid, "timestamp": timestamp},
            UpdateExpression="SET queries_count = queries_count + :one, conversation_history = list_append(conversation_history, :entry)",
            ExpressionAttributeValues={
                ":one": 1,
                ":entry": [{"query": query, "answer": answer, "language": language,
                            "ts": int(datetime.now().timestamp())}]
            }
        )
    except Exception as e:
        logger.warning(f"Failed to log query: {e}")


def get_call_timestamp(call_sid: str) -> int:
    try:
        result = calls_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("call_id").eq(call_sid),
            Limit=1
        )
        items = result.get("Items", [])
        return items[0]["timestamp"] if items else 0
    except:
        return 0


def twiml_response(twiml: VoiceResponse) -> dict:
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/xml"},
        "body": str(twiml)
    }
