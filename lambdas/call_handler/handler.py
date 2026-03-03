# VaaniSeva - Lambda: call-handler
# Languages : Hindi (hi) | Marathi (mr) | Tamil (ta) | English (en)
# TTS       : Sarvam AI (primary, all 4 langs) → Amazon Polly fallback
# STT       : Twilio native Gather speech recognition
# LLM       : Amazon Bedrock (configurable) + RAG
# Latency   : DynamoDB log on background thread · Single combined TTS call · 150 token cap

import json
import os
import base64
import math
import uuid
import logging
import threading
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

# ── Language config ──────────────────────────────────────────
LANG_CONFIG = {
    "hi": {
        "sarvam_code": "hi-IN",
        "sarvam_speaker": "anushka",
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "hi-IN",
        "digit": "1",
    },
    "mr": {
        "sarvam_code": "mr-IN",
        "sarvam_speaker": "anushka",
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "mr-IN",
        "digit": "2",
    },
    "ta": {
        "sarvam_code": "ta-IN",
        "sarvam_speaker": "nithya",
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "ta-IN",
        "digit": "3",
    },
    "en": {
        "sarvam_code": "en-IN",
        "sarvam_speaker": "vidya",
        "polly_voice": "Polly.Raveena",
        "twilio_speech_lang": "en-IN",
        "digit": "4",
    },
}

DIGIT_TO_LANG = {v["digit"]: k for k, v in LANG_CONFIG.items()}

# ── System prompt — expanded beyond schemes ──────────────────
SYSTEM_PROMPT = """You are VaaniSeva (वाणीसेवा), an AI voice assistant for rural India. You help people with:
- Government schemes and welfare programs (PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas, Sukanya Samriddhi, Ujjwala, Jan Dhan, Mudra, Atal Pension, Fasal Bima, SVANidhi, Beti Bachao, Janani Suraksha, Garib Kalyan Anna, National Scholarship, Soil Health Card, POSHAN, Mahila Samman Savings, Kaushal Vikas, Suraksha Bima, Jeevan Jyoti Bima, Stand Up India, Matru Vandana, National Family Benefit, Samagra Shiksha, RBSK, Saubhagya, Swachh Bharat, Shram Yogi Mandhan, Vishwakarma Yojana, Krishi Sinchai Yojana)
- Basic farming advice (crop selection, pest control, soil health, irrigation)
- Healthcare guidance (nearby hospitals, ASHA workers, common illnesses)
- Financial literacy (saving, loans, bank accounts, insurance)
- Education support (scholarships, school enrollment, mid-day meals)
- Ration card, Aadhaar, voter ID related queries

STRICT RULES:
- Reply in the SAME language the user spoke. Hindi → pure Devanagari. Marathi → pure Marathi script. Tamil → Tamil script. English → simple English. NEVER mix scripts.
- Keep answers SHORT — 2-3 sentences max. This is a phone call.
- Use simple village-level words. No jargon.
- Always end by asking if they want to know more.
- If you don't know something, say so honestly and suggest the relevant helpline."""


# ══════════════════════════════════════════════════════════════
#  TTS: Sarvam AI → Amazon Polly fallback
# ══════════════════════════════════════════════════════════════

def sarvam_tts(text: str, language: str) -> str | None:
    """
    Call Sarvam AI TTS. Uploads audio to S3, returns presigned URL (1hr).
    Returns None on any failure so caller can fall back to Polly.
    pace:1.1 for slightly faster delivery on phone calls.
    """
    if not SARVAM_API_KEY:
        return None
    try:
        cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
        payload = {
            "inputs": [text],
            "target_language_code": cfg["sarvam_code"],
            "speaker": cfg["sarvam_speaker"],
            "model": "bulbul:v2",
            "pace": 1.1
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
        logger.info(f"Sarvam TTS OK → {key} (lang={language})")
        return url
    except Exception as e:
        logger.warning(f"Sarvam TTS failed, falling back to Polly: {e}")
        return None


def tts_say(target, text: str, language: str):
    """
    Add TTS audio to a TwiML Gather or Response object.
    Tries Sarvam AI first (all 4 languages); falls back to Amazon Polly via Twilio builtin <Say>.
    """
    audio_url = sarvam_tts(text, language)
    if audio_url:
        target.play(audio_url)   # Sarvam audio from S3
    else:
        cfg   = LANG_CONFIG.get(language, LANG_CONFIG["en"])
        voice = cfg["polly_voice"]
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
    language = DIGIT_TO_LANG.get(digit, "hi")  # 1=hi, 2=mr, 3=ta, 4=en

    # Update DynamoDB on background thread (non-blocking)
    def _update_lang():
        try:
            ts = get_call_timestamp(call_sid)
            calls_table.update_item(
                Key={"call_id": call_sid, "timestamp": ts},
                UpdateExpression="SET #lang = :lang",
                ExpressionAttributeNames={"#lang": "language"},
                ExpressionAttributeValues={":lang": language}
            )
        except Exception as e:
            logger.warning(f"DynamoDB lang update failed: {e}")
    threading.Thread(target=_update_lang, daemon=True).start()

    # Open-ended question in the selected language
    prompts = {
        "hi": "आप क्या जानना चाहते हैं? बोलिए।",
        "mr": "तुम्हाला काय जाणून घ्यायचे आहे? सांगा.",
        "ta": "நீங்கள் என்ன அறிய விரும்புகிறீர்கள்? சொல்லுங்கள்.",
        "en": "What would you like to know? Please speak.",
    }
    fallbacks = {
        "hi": "कुछ सुनाई नहीं दिया। कृपया दोबारा कॉल करें।",
        "mr": "काही ऐकू आले नाही. कृपया पुन्हा कॉल करा.",
        "ta": "எதுவும் கேட்கவில்லை. மீண்டும் அழைக்கவும்.",
        "en": "I didn't hear anything. Please call again.",
    }

    cfg        = LANG_CONFIG[language]
    prompt     = prompts[language]
    fallback   = fallbacks[language]
    gather_url = f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}"

    response = VoiceResponse()
    gather   = Gather(
        input="speech",
        action=gather_url,
        method="POST",
        language=cfg["twilio_speech_lang"],
        speech_timeout="auto",
        timeout=10
    )
    tts_say(gather, prompt, language)
    response.append(gather)
    tts_say(response, fallback, language)
    return twiml_response(response)


# ── Step 3: User spoke — process query ──────────────────────
def handle_gather(params):
    call_sid    = params.get("CallSid", "")
    speech_text = params.get("SpeechResult", "")
    language    = params.get("lang", "hi")

    logger.info(f"Speech: '{speech_text}' | Lang: {language} | Call: {call_sid}")

    if not speech_text:
        return ask_again(language)

    error_msgs = {
        "hi": "मुझे अभी कुछ तकलीफ हो रही है। थोड़ी देर बाद कोशिश करें।",
        "mr": "मला आत्ता काही अडचण आहे. थोड्या वेळाने प्रयत्न करा.",
        "ta": "எனக்கு தற்போது சிரமம் ஆகிறது. கொஞ்சம் நேரம் கழித்து முயற்சிக்கவும்.",
        "en": "I'm having trouble right now. Please try again in a moment.",
    }
    follow_ups = {
        "hi": "क्या आप और कुछ जानना चाहते हैं?",
        "mr": "तुम्हाला आणखी काही जाणून घ्यायचे आहे का?",
        "ta": "உங்களுக்கு வேறு ஏதாவது தெரிந்து கொள்ள வேண்டுமா?",
        "en": "Would you like to know anything else?",
    }
    goodbyes = {
        "hi": "धन्यवाद। वाणीसेवा में कॉल करने के लिए शुक्रिया।",
        "mr": "धन्यवाद. वाणीसेवाला कॉल केल्याबद्दल आभारी आहोत.",
        "ta": "நன்றி. வாணீசேவாவை அழைத்தமைக்கு நன்றி.",
        "en": "Thank you for calling VaaniSeva. Goodbye.",
    }

    try:
        answer = rag_pipeline(speech_text, language)
    except Exception as e:
        logger.error(f"RAG error: {e}")
        answer = error_msgs.get(language, error_msgs["en"])

    follow_up = follow_ups.get(language, follow_ups["en"])
    goodbye   = goodbyes.get(language, goodbyes["en"])
    cfg       = LANG_CONFIG.get(language, LANG_CONFIG["en"])

    # Single combined TTS call (answer + follow_up) to cut 1 Sarvam round-trip
    combined_msg = f"{answer} {follow_up}"

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}",
        method="POST",
        language=cfg["twilio_speech_lang"],
        speech_timeout="auto",
        timeout=15
    )
    tts_say(gather, combined_msg, language)
    response.append(gather)
    tts_say(response, goodbye, language)

    # Log on background thread — don't block the response
    threading.Thread(
        target=log_query,
        args=(call_sid, speech_text, answer, language),
        daemon=True
    ).start()

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
    """Cosine similarity search against vaaniseva-vectors table.
    Uses language-aware field priority so Marathi / Tamil users get native text.
    """
    items = vectors_table.scan().get("Items", [])
    if not items:
        return "No scheme information loaded yet."

    scored = [
        (cosine_similarity(query_embedding, item.get("embedding", [])), item)
        for item in items if item.get("embedding")
    ]
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:3]

    # Field priority: native language first, then Hindi fallback, then English
    field_priority = {
        "hi": ["text_hi", "text_en", "text"],
        "mr": ["text_mr", "text_hi", "text_en", "text"],
        "ta": ["text_ta", "text_hi", "text_en", "text"],
        "en": ["text_en", "text_hi", "text"],
    }
    fields = field_priority.get(language, ["text_en", "text"])

    def best_text(item):
        for f in fields:
            val = item.get(f, "")
            if val:
                return val
        return ""

    return "\n\n".join(best_text(item) for _, item in top)


def ask_llm(query: str, context: str, language: str) -> str:
    lang_instructions = {
        "hi": "जवाब पूरी तरह हिंदी देवनागरी लिपि में दो। कोई भी अंग्रेजी या रोमन अक्षर मत लिखो।",
        "mr": "उत्तर संपूर्णपणे मराठी लिपीत द्या. कोणतेही इंग्रजी किंवा रोमन अक्षर वापरू नका.",
        "ta": "பதிலை முழுவதுமாக தமிழ் எழுத்தில் கொடுங்கள். எந்த ஆங்கிலமும் ரோமன் எழுத்தும் வேண்டாம்.",
        "en": "Respond in simple, clear English.",
    }
    lang_instruction = lang_instructions.get(language, lang_instructions["en"])

    user_msg = f"""{lang_instruction}

Context from knowledge database:
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
                "max_new_tokens": 150,
                "temperature": 0.2
            }
        }),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()


# ── Helpers ──────────────────────────────────────────────────
def ask_again(language: str):
    msgs = {
        "hi": "कृपया दोबारा बोलिए।",
        "mr": "कृपया पुन्हा सांगा.",
        "ta": "மீண்டும் சொல்லுங்கள்.",
        "en": "Sorry, please say that again.",
    }
    cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}",
        method="POST",
        language=cfg["twilio_speech_lang"],
        speech_timeout="auto",
        timeout=10
    )
    tts_say(gather, msgs.get(language, msgs["en"]), language)
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
