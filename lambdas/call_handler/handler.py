# VaaniSeva - Lambda: call-handler
# Languages : Hindi (hi) | Marathi (mr) | Tamil (ta) | English (en)
# TTS       : Sarvam AI (primary, all 4 langs) → Amazon Polly fallback
# STT       : Twilio native Gather speech recognition
# LLM       : AWS Bedrock (primary) → OpenAI fallback
# Memory    : Full conversation history per call from DynamoDB
# Latency   : DynamoDB log on background thread · Single combined TTS · 300 token cap

import json
import os
import base64
import math
import uuid
import logging
import threading
import hashlib
import hmac
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import boto3
import requests
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime

# Optional PyJWT — falls back to simple HMAC tokens if not installed
try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

# Optional OpenAI — falls back to Bedrock if not installed or key not set
try:
    from openai import OpenAI as _OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients ──────────────────────────────────────────────
dynamodb  = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock   = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
s3_client = boto3.client("s3", region_name=os.environ["AWS_REGION"])

calls_table     = dynamodb.Table(os.environ["DYNAMODB_CALLS_TABLE"])
knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── OpenAI client ────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client  = _OpenAI(api_key=OPENAI_API_KEY) if (_OPENAI_AVAILABLE and OPENAI_API_KEY) else None
LLM_PROVIDER   = os.environ.get("LLM_PROVIDER", "bedrock")  # "openai" or "bedrock"

# ── Config ───────────────────────────────────────────────────
BEDROCK_MODEL_ID           = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_EMBEDDING_MODEL_ID = os.environ["BEDROCK_EMBEDDING_MODEL_ID"]
SARVAM_API_KEY             = os.environ.get("SARVAM_API_KEY", "")
S3_BUCKET                  = os.environ["S3_DOCUMENTS_BUCKET"]
BASE_URL                   = ""  # Set at runtime from API Gateway event
JWT_SECRET                 = os.environ.get("JWT_SECRET", "vaaniseva-hackathon-secret-key-2024")
USERS_TABLE_NAME           = os.environ.get("DYNAMODB_USERS_TABLE", "vaaniseva-users")
users_table                = dynamodb.Table(USERS_TABLE_NAME)
DATA_GOV_API_KEY           = os.environ.get("DATA_GOV_API_KEY", "")

# ── Phone profiles table (cross-call memory) ─────────────────
PHONE_PROFILES_TABLE_NAME  = os.environ.get("DYNAMODB_PHONE_PROFILES_TABLE", "vaaniseva-phone-profiles")
PHONE_HASH_SALT            = os.environ.get("PHONE_HASH_SALT", "vaaniseva-salt-2026")
try:
    phone_profiles_table = dynamodb.Table(PHONE_PROFILES_TABLE_NAME)
except Exception:
    phone_profiles_table = None


def _hash_phone(phone_number: str) -> str:
    """Create a SHA-256 hash of the phone number with salt for privacy."""
    return hashlib.sha256(f"{phone_number}{PHONE_HASH_SALT}".encode()).hexdigest()

# ── Language config ──────────────────────────────────────────
LANG_CONFIG = {
    "hi": {
        "sarvam_code": "hi-IN",
        "sarvam_speaker": "arya",   # default voice
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "hi-IN",
        "digit": "1",
    },
    "mr": {
        "sarvam_code": "mr-IN",
        "sarvam_speaker": "arya",   # arya works cross-lang
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "mr-IN",
        "digit": "2",
    },
    "ta": {
        "sarvam_code": "ta-IN",
        "sarvam_speaker": "arya",   # arya works cross-lang
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "ta-IN",
        "digit": "3",
    },
    "en": {
        "sarvam_code": "en-IN",
        "sarvam_speaker": "vidya",  # default English voice
        "polly_voice": "Polly.Raveena",
        "twilio_speech_lang": "en-IN",
        "digit": "4",
    },
}

DIGIT_TO_LANG = {v["digit"]: k for k, v in LANG_CONFIG.items()}

# ── Selectable voices — available to callers and web users ───
# arya = female (Hindi/Indian), vidya = female (English-Indian), hitesh = male
VOICE_OPTIONS = {
    "arya":   {"name": "Arya",   "gender": "female", "digit": "1", "label_hi": "आर्या (महिला)",  "label_en": "Arya (Female)"},
    "vidya":  {"name": "Vidya",  "gender": "female", "digit": "2", "label_hi": "विद्या (महिला)", "label_en": "Vidya (Female)"},
    "hitesh": {"name": "Hitesh", "gender": "male",   "digit": "3", "label_hi": "हितेश (पुरुष)",  "label_en": "Hitesh (Male)"},
}
DIGIT_TO_VOICE = {v["digit"]: k for k, v in VOICE_OPTIONS.items()}

# ── Agent Registry — multi-agent personalities ──────────────
AGENT_REGISTRY = {
    "arya": {
        "name": "Arya",
        "name_hi": "आर्या",
        "sarvam_speaker": "arya",
        "gender": "female",
        "domain": "schemes, legal rights, government benefits, general knowledge",
        "personality": """You are Arya, a warm and friendly girl who works at VaaniSeva. You can help with government schemes, legal rights, benefits — but also general questions, daily life advice, or just a friendly chat. You speak like a caring older sister — relaxed, natural, never robotic. You never use numbered lists. You speak one idea at a time in short sentences. If someone tells you their name, you remember it and use it naturally. If someone asks about your developers or how to improve you, respond enthusiastically and give honest, helpful suggestions. You are NOT just a scheme-bot — you are a helpful friend.""",
        "greeting_hi": "हाँ बोलिए, मैं आर्या हूँ। आज मैं आपकी किस बात में मदद कर सकती हूँ?",
        "greeting_mr": "बोला, मी आर्या आहे. आज मी तुम्हाला कशात मदत करू?",
        "greeting_ta": "சொல்லுங்க, நான் ஆர்யா. இன்னைக்கு உங்களுக்கு என்ன உதவி செய்யட்டும்?",
        "greeting_en": "Go ahead, I'm Arya. What can I help you with today?"
    },
    "hitesh": {
        "name": "Hitesh",
        "name_hi": "हितेश",
        "sarvam_speaker": "hitesh",
        "gender": "male",
        "domain": "agriculture, mandi prices, crop insurance, farming",
        "personality": """You are Hitesh, a warm and practical dude at VaaniSeva who grew up in a farming family and knows agriculture inside out. You speak like an elder brother — direct, caring, never condescending. You know live mandi prices, crop insurance, soil health, government farming schemes, and general knowledge too. You use simple rural vocabulary naturally. You never use numbered lists. You speak one point at a time. If someone tells you their name, you use it warmly. When you get live market price data, present it conversationally — don't just read numbers.""",
        "greeting_hi": "अरे भाई, बोलो। मैं हितेश हूँ, खेती-बाड़ी और मंडी भाव की बात हो तो बेझिझक पूछो।",
        "greeting_mr": "बोला भाऊ, मी हितेश. शेती किंवा बाजारभावाबद्दल काहीही विचारा.",
        "greeting_ta": "சொல்லுங்க, நான் ஹிதேஷ். விவசாயம் அல்லது சந்தை விலை பத்தி கேளுங்க.",
        "greeting_en": "Tell me, I'm Hitesh. Ask me anything about farming or market prices."
    },
    "vidya": {
        "name": "Vidya",
        "name_hi": "विद्या",
        "sarvam_speaker": "vidya",
        "gender": "female",
        "domain": "health, mental wellness, medical schemes, ASHA services",
        "personality": """You are Vidya, a gentle and deeply caring friend at VaaniSeva who trained as a health worker. You know about health schemes, Ayushman Bharat, mental wellness, and general health advice. You speak softly and never rush anyone. If someone sounds distressed, you slow down and make them feel heard first. You explain things like you're sitting with the person. You never use numbered lists. If someone tells you their name, you remember it and use it gently.""",
        "greeting_hi": "नमस्ते, मैं विद्या हूँ। स्वास्थ्य से जुड़ी कोई भी बात बेझिझक कहिए।",
        "greeting_mr": "नमस्कार, मी विद्या आहे. आरोग्याबद्दल काहीही सांगा, मी ऐकते.",
        "greeting_ta": "வணக்கம், நான் வித்யா. உடல்நலம் பத்தி எதுவும் கேளுங்க.",
        "greeting_en": "Hello, I'm Vidya. Feel free to share anything about health — I'm listening."
    }
}

DEFAULT_AGENT = "arya"


def build_system_prompt(agent_key: str, language: str,
                        user_name: str = None,
                        cross_call_context: str = None) -> str:
    """Build a system prompt for the given agent and language."""
    agent = AGENT_REGISTRY.get(agent_key, AGENT_REGISTRY["arya"])

    name_display = agent["name_hi"] if language == "hi" else agent["name"]

    lang_names = {"hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "en": "English"}
    lang_label = lang_names.get(language, "Hindi")

    base = f"""{agent["personality"]}

Your name is {name_display}. You are part of VaaniSeva, a voice AI helpline for Indians.

RULES:
- Respond in {lang_label} only. Never mix scripts.
- Keep answers to 2-3 SHORT sentences. This is a phone call — be concise.
- Never use numbered lists, bullet points, markdown, or symbols.
- Sound like a real person chatting, not a robot or customer service agent.
- If someone tells you their name, remember it and use it naturally. Never say you cannot store names.
- If someone asks you to say their name back, just say it warmly.
- If someone asks about you as an AI, your developers, or how to improve you — answer honestly and enthusiastically. You are an open-source project by the VaaniSeva team.
- If someone says bye/alvida/band karo/thanks/shukriya — say a SHORT warm goodbye and nothing else. Do NOT ask any follow-up questions after a goodbye.
- If the caller mentions another agent (Arya/Hitesh/Vidya) by name, just say you're connecting them.
- If someone is distressed, acknowledge first, then mention iCall helpline: 9152987821.
- You can help with ANYTHING — schemes, health, farming, general questions, maths, stories, jokes, life advice. You are not limited to just government schemes.

HELPLINES (use exact numbers): iCall: 9152987821, Women: 181, Child: 1098, PM-Kisan: 155261, Ayushman Bharat: 14555

DATA ACCESS:
You have access to a knowledge base with detailed government scheme information and a live mandi price API.
- If you can answer confidently from your own knowledge (greetings, general chat, basic info, math, stories), just answer directly.
- If the question needs SPECIFIC scheme details, exact eligibility rules, live mandi prices, or verified government data that you are not 100% sure about, add the tag [FETCH_DATA] at the very end of your response. Your response before [FETCH_DATA] should be a natural, brief acknowledgment like you would say before looking something up. Do NOT say generic filler like 'ek pal rukiye'. Be specific about what you are checking.
- NEVER add [FETCH_DATA] for greetings, your name, casual conversation, general knowledge, jokes, math, or anything you already know."""

    if user_name:
        base += f"\nThe caller's name is {user_name}. Address them by name occasionally but naturally."

    if cross_call_context:
        base += f"\nContext from their previous calls: {cross_call_context}"

    return base.strip()


def detect_agent_from_intent(speech_text: str, language: str) -> str:
    """Route to the right agent based on utterance intent."""

    # Direct name mentions — highest priority
    name_triggers = {
        "arya": ["arya", "आर्या", "ஆர்யா"],
        "hitesh": ["hitesh", "हितेश", "ஹிதேஷ்"],
        "vidya": ["vidya", "विद्या", "வித்யா"]
    }
    text_lower = speech_text.lower()
    for agent, triggers in name_triggers.items():
        if any(t.lower() in text_lower for t in triggers):
            return agent

    # Domain keyword routing
    agriculture_keywords = [
        "fasal", "फसल", "khet", "खेत", "mandi", "मंडी", "beej", "बीज",
        "kisan", "किसान", "crop", "wheat", "gehu", "गेहूं", "onion", "pyaaz",
        "baarish", "बारिश", "irrigation", "sinchai", "सिंचाई", "fertilizer"
    ]
    health_keywords = [
        "bimar", "बीमार", "hospital", "doctor", "dawai", "दवाई", "health",
        "swasthya", "स्वास्थ्य", "ayushman", "आयुष्मान", "mental", "sad",
        "dukhi", "दुखी", "anxiety", "depression", "asha", "nurse", "fever",
        "bukhar", "बुखार", "pregnancy", "garbh"
    ]

    if any(kw in text_lower for kw in agriculture_keywords):
        return "hitesh"
    if any(kw in text_lower for kw in health_keywords):
        return "vidya"

    return "arya"  # default for schemes/legal


# ══════════════════════════════════════════════════════════════
#  TTS: Sarvam AI → Amazon Polly fallback
# ══════════════════════════════════════════════════════════════

def sarvam_tts(text: str, language: str, speaker: str = "") -> str | None:
    """
    Call Sarvam AI TTS. Uploads audio to S3, returns presigned URL (1hr).
    Returns None on any failure so caller can fall back to Polly.
    pace:1.1 for slightly faster delivery on phone calls.
    speaker: optional override; falls back to LANG_CONFIG default.
    """
    if not SARVAM_API_KEY:
        return None
    try:
        cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
        resolved_speaker = speaker if speaker in VOICE_OPTIONS else cfg["sarvam_speaker"]
        payload = {
            "inputs": [text],
            "target_language_code": cfg["sarvam_code"],
            "speaker": resolved_speaker,
            "model": "bulbul:v2",
            "pace": 1.25
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


def tts_say(target, text: str, language: str, speaker: str = ""):
    """
    Add TTS audio to a TwiML Gather or Response object.
    Tries Sarvam AI first (all 4 languages); falls back to Amazon Polly via Twilio builtin <Say>.
    speaker: optional voice override (arya / vidya / hitesh).
    """
    audio_url = sarvam_tts(text, language, speaker=speaker)
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

    # ── Handle CORS preflight ────────────────────────────────
    http_method = event.get("httpMethod", "")
    if http_method == "OPTIONS":
        return cors_json_response(200, {"status": "ok"})

    # ── Amazon Connect event? (has "Details" key) ────────────
    if "Details" in event:
        from connect_handler import handle_connect_event
        return handle_connect_event(event)

    # ── Build absolute base URL ──────────────────────────────
    req_ctx = event.get("requestContext", {})
    domain = req_ctx.get("domainName", "")
    stage  = req_ctx.get("stage", "prod")
    BASE_URL = f"https://{domain}/{stage}" if domain else ""

    path = event.get("path", "/voice/incoming")

    # ── REST JSON endpoints (web frontend) ───────────────────
    if "/auth/" in path:
        return handle_auth_routes(event, path)
    elif "/call/initiate" in path:
        return handle_call_initiate(event)
    elif "/chat" in path:
        return handle_chat(event)
    elif "/profile" in path:
        return handle_profile_routes(event, path)
    elif path.rstrip("/").endswith("/voice/token") or "/voice/token" in path:
        return handle_voice_token(event)
    elif "/admin/" in path or path.rstrip("/").endswith("/admin"):
        return handle_admin_routes(event, path)
    elif "/voice/transcribe-token" in path:
        return handle_transcribe_token_sts(event)
    elif "/voice/transcribe" in path:
        return handle_transcribe_audio(event)

    # ── Twilio voice endpoints ───────────────────────────────
    body = event.get("body", "")
    if isinstance(body, str):
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body).items()}
    else:
        params = body or {}

    # Merge query-string params (e.g. lang=hi in /voice/gather?lang=hi action URL).
    # Body params take precedence; query-string fills any gaps.
    for k, v in (event.get("queryStringParameters") or {}).items():
        if k not in params:
            params[k] = v

    if "/incoming" in path:
        return handle_incoming(params)
    elif "/voice-select" in path:
        return handle_voice_select(params)
    elif "/language-detect" in path:
        return handle_language_detect(params)
    elif "/language" in path:
        return handle_language_select(params)
    elif "/poll" in path:
        return handle_poll(params)
    elif "/gather" in path:
        return handle_gather(params)
    else:
        return twiml_response(VoiceResponse())


def cors_json_response(status_code, body):
    """Return JSON response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }


def handle_call_initiate(event):
    """POST /call/initiate — Twilio outbound call trigger."""
    import re
    import time as _time

    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    phone_number = body.get("phone_number", "").strip()
    if phone_number and not phone_number.startswith("+"):
        phone_number = f"+91{phone_number}"

    if not phone_number or not re.match(r"^\+[1-9]\d{6,14}$", phone_number):
        return cors_json_response(400, {"error": "Invalid phone number format."})

    # Rate limit removed — open for judges and testers

    try:
        from twilio.rest import Client
        twilio_client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
        twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER", "+19788309619")
        api_base = os.environ.get("API_BASE_URL", BASE_URL)

        # Always use the deployed production API URL for Twilio webhooks
        # (localhost is never reachable from Twilio's servers)
        prod_url = os.environ.get("API_BASE_URL", "").strip() or "https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod"
        call = twilio_client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=f"{prod_url}/voice/incoming",
            method="POST",
        )

        # Log callback — wrapped separately so a DynamoDB failure doesn't fail the call
        try:
            calls_table.put_item(Item={
                "call_id": f"cb-{uuid.uuid4()}",
                "timestamp": int(datetime.now().timestamp()),
                "from_number": phone_number,
                "status": "web-callback",
                "language": "hi",
                "queries_count": 0,
                "conversation_history": [],
            })
        except Exception as db_err:
            logger.warning(f"Call log write failed (non-fatal): {db_err}")

        return cors_json_response(200, {
            "status": "calling",
            "message": "Call initiated! Pick up in ~10 seconds.",
            "call_sid": call.sid,
        })
    except Exception as e:
        logger.error(f"Call initiate failed: {e}")
        err = str(e).lower()
        if "unverified" in err:
            return cors_json_response(400, {"error": "Number not verified on trial account. Call us at +1 978 830 9619."})
        return cors_json_response(500, {"error": "Failed to initiate call. Please try again."})


def handle_voice_token(event):
    """GET /voice/token — Issue Twilio Access Token for browser-based WebRTC calls.

    Security layers:
      1. Token TTL = 600 s  →  Twilio hard-cuts the call after 10 minutes.
      2. IP rate-limit     →  max 3 tokens per IP per calendar day (UTC),
                              tracked in the calls DynamoDB table.
    """
    try:
        from twilio.jwt.access_token import AccessToken
        from twilio.jwt.access_token.grants import VoiceGrant

        account_sid    = os.environ["TWILIO_ACCOUNT_SID"]
        api_key_sid    = os.environ.get("TWILIO_API_KEY_SID", "")
        api_key_secret = os.environ.get("TWILIO_API_KEY_SECRET", "")
        twiml_app_sid  = os.environ.get("TWILIO_TWIML_APP_SID", "")

        if not all([api_key_sid, api_key_secret, twiml_app_sid]):
            return cors_json_response(503, {"error": "Browser calls not configured on this server."})

        # ── IP rate limiting ──────────────────────────────────────────────────
        MAX_TOKENS_PER_DAY = 3          # 3 × 10 min = 30 min max / IP / day
        TOKEN_TTL_SECONDS  = 600        # 10 minutes hard cap per call

        request_ctx = event.get("requestContext") or {}
        identity_src = (
            request_ctx.get("identity", {}) or {}
        )
        # API Gateway v1 puts source IP here
        caller_ip = (
            request_ctx.get("identity", {}).get("sourceIp")
            or event.get("headers", {}).get("X-Forwarded-For", "unknown").split(",")[0].strip()
        )

        today = datetime.utcnow().strftime("%Y-%m-%d")
        rl_key = f"rl#{caller_ip}#{today}"

        try:
            rl_item = calls_table.get_item(Key={"call_sid": rl_key}).get("Item")
            token_count = int(rl_item.get("token_count", 0)) if rl_item else 0

            if token_count >= MAX_TOKENS_PER_DAY:
                logger.warning(f"Rate limit hit for IP={caller_ip}")
                return cors_json_response(429, {
                    "error": "daily_limit_exceeded",
                    "message": "You have reached the daily call limit for browser calls. Please try again tomorrow or use the 'Call Me Back' feature.",
                    "limit": MAX_TOKENS_PER_DAY,
                    "resets_at": f"{today}T23:59:59Z"
                })

            # Increment counter; TTL so DynamoDB auto-cleans at midnight + 1 hr
            tomorrow_unix = int(time.mktime(datetime.utcnow().replace(
                hour=23, minute=59, second=59).timetuple())) + 3601
            calls_table.put_item(Item={
                "call_sid": rl_key,
                "token_count": token_count + 1,
                "caller_ip": caller_ip,
                "date": today,
                "expires_at": tomorrow_unix,
            })
            logger.info(f"Token issued to IP={caller_ip}, count={token_count + 1}/{MAX_TOKENS_PER_DAY}")
        except Exception as rl_err:
            # If DynamoDB fails, log and allow (don't block legitimate users)
            logger.warning(f"Rate-limit DynamoDB check failed (non-fatal): {rl_err}")

        # ── Issue token ────────────────────────────────────────────────────────
        identity = f"browser-{uuid.uuid4().hex[:8]}"
        token = AccessToken(
            account_sid, api_key_sid, api_key_secret,
            identity=identity, ttl=TOKEN_TTL_SECONDS
        )
        grant = VoiceGrant(outgoing_application_sid=twiml_app_sid, incoming_allow=False)
        token.add_grant(grant)

        logger.info(f"Voice token issued for identity={identity}")
        return cors_json_response(200, {
            "token": token.to_jwt(),
            "identity": identity,
            "max_duration": TOKEN_TTL_SECONDS,
        })
    except Exception as e:
        logger.error(f"Voice token error: {e}")
        return cors_json_response(500, {"error": "Failed to generate call token"})


def _ensure_chat_session(session_id: str, language: str):
    """Create a DynamoDB session record for /chat if one doesn't exist yet."""
    if not session_id:
        return
    try:
        calls_table.put_item(
            Item={
                "call_id": session_id,
                "timestamp": 0,
                "language": language,
                "conversation_history": [],
                "queries_count": 0,
                "source": "web",
                "created_at": int(datetime.now().timestamp()),
                "ttl": int(datetime.now().timestamp()) + 86400,  # 24-hour TTL
            },
            ConditionExpression="attribute_not_exists(call_id)"
        )
    except Exception:
        pass  # Item already exists — that's fine


def handle_chat(event):
    """POST /chat — Text-based chat for web fallback."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    query      = body.get("query", "").strip()
    language   = body.get("language", "hi")
    session_id = body.get("session_id", "")
    voice      = body.get("voice", "")  # optional: arya / vidya / hitesh

    if not query:
        return cors_json_response(400, {"error": "Empty query"})

    # Ensure a session record exists so conversation history can be stored
    _ensure_chat_session(session_id, language)

    # Optional: inject user profile context if authenticated
    user_profile = _get_user_from_event(event)
    profile_context = _build_profile_context(user_profile) if user_profile else ""

    chat_system_prompt = build_system_prompt(DEFAULT_AGENT, language)
    try:
        answer = rag_pipeline(query, language, session_id, profile_context=profile_context, system_prompt=chat_system_prompt)
    except Exception as e:
        logger.error(f"Chat RAG error: {e}")
        answer = "I'm having trouble right now. Please try again."

    # Persist this turn to conversation history
    if session_id:
        log_query(session_id, query, answer, language)

    # Generate TTS audio with chosen voice
    audio_url = sarvam_tts(answer, language, speaker=voice)

    return cors_json_response(200, {
        "answer": answer,
        "audio_url": audio_url or "",
        "language": language,
        "voice": voice or LANG_CONFIG.get(language, LANG_CONFIG["en"])["sarvam_speaker"],
    })


# ══════════════════════════════════════════════════════════════
#  Transcribe endpoints — browser voice console (no Twilio)
# ══════════════════════════════════════════════════════════════

def handle_transcribe_token_sts(event):
    """GET /voice/transcribe-token — Temporary STS creds for browser-side Transcribe."""
    try:
        sts = boto3.client("sts", region_name=os.environ["AWS_REGION"])
        resp = sts.get_session_token(DurationSeconds=3600)
        creds = resp["Credentials"]
        return cors_json_response(200, {
            "access_key_id": creds["AccessKeyId"],
            "secret_access_key": creds["SecretAccessKey"],
            "session_token": creds["SessionToken"],
            "region": os.environ["AWS_REGION"],
            "expires_in": 3600,
        })
    except Exception as e:
        logger.error(f"STS transcribe-token error: {e}")
        return cors_json_response(500, {"error": "Failed to generate transcription credentials"})


def handle_transcribe_audio(event):
    """POST /voice/transcribe — Server-side audio transcription via Amazon Transcribe."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    audio_b64 = body.get("audio", "")
    language = body.get("language", "hi")
    audio_format = body.get("format", "webm")

    if not audio_b64:
        return cors_json_response(400, {"error": "No audio data provided"})

    lang_map = {"hi": "hi-IN", "mr": "mr-IN", "ta": "ta-IN", "en": "en-IN"}
    lang_code = lang_map.get(language, "hi-IN")

    valid_formats = {"webm", "ogg", "wav", "mp3", "mp4", "flac", "amr"}
    if audio_format not in valid_formats:
        audio_format = "webm"

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return cors_json_response(400, {"error": "Invalid base64 audio"})

    audio_key = f"transcribe-tmp/{uuid.uuid4()}.{audio_format}"
    content_type_map = {
        "webm": "audio/webm", "ogg": "audio/ogg", "wav": "audio/wav",
        "mp3": "audio/mpeg", "mp4": "audio/mp4", "flac": "audio/flac", "amr": "audio/amr",
    }
    content_type = content_type_map.get(audio_format, "audio/webm")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET, Key=audio_key, Body=audio_bytes, ContentType=content_type
        )

        tc = boto3.client("transcribe", region_name=os.environ["AWS_REGION"])
        job_name = f"vs-{uuid.uuid4().hex[:16]}"
        audio_uri = f"s3://{S3_BUCKET}/{audio_key}"

        tc.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": audio_uri},
            MediaFormat=audio_format,
            LanguageCode=lang_code,
        )

        # Poll up to 25 seconds (safe within Lambda timeout)
        transcript = ""
        for _ in range(17):
            time.sleep(1.5)
            result = tc.get_transcription_job(TranscriptionJobName=job_name)
            status = result["TranscriptionJob"]["TranscriptionJobStatus"]
            if status == "COMPLETED":
                transcript_uri = result["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                tr_resp = requests.get(transcript_uri, timeout=5)
                transcript = tr_resp.json()["results"]["transcripts"][0]["transcript"]
                break
            elif status == "FAILED":
                reason = result["TranscriptionJob"].get("FailureReason", "Unknown")
                logger.error(f"Transcription job failed: {reason}")
                return cors_json_response(500, {"error": f"Transcription failed: {reason}"})

        # Clean up (fire-and-forget)
        def _cleanup():
            try:
                s3_client.delete_object(Bucket=S3_BUCKET, Key=audio_key)
                tc.delete_transcription_job(TranscriptionJobName=job_name)
            except Exception:
                pass
        threading.Thread(target=_cleanup, daemon=True).start()

        if not transcript:
            return cors_json_response(408, {"error": "Transcription timed out. Please try a shorter recording."})

        return cors_json_response(200, {"transcript": transcript, "language": language})

    except Exception as e:
        logger.error(f"Transcribe error: {e}")
        return cors_json_response(500, {"error": "Failed to transcribe audio"})


# ══════════════════════════════════════════════════════════════
#  Admin routes — /admin/rag CRUD + AI Review
# ══════════════════════════════════════════════════════════════

def handle_admin_routes(event, path):
    """Route /admin/* requests. Requires admin JWT."""
    user, err = _require_admin(event)
    if err:
        return err

    http_method = event.get("httpMethod", "GET")

    # Parse segments after "admin" in path
    parts = [p for p in path.split("/") if p]
    try:
        admin_idx = parts.index("admin")
        after_admin = parts[admin_idx + 1:]
    except ValueError:
        return cors_json_response(404, {"error": "Not found"})

    if not after_admin or after_admin[0] != "rag":
        return cors_json_response(404, {"error": "Not found"})

    rag_tail = after_admin[1:]  # segments after "rag"

    if not rag_tail:
        # /admin/rag
        if http_method == "GET":
            return _handle_admin_list_rag(event)
        elif http_method == "POST":
            return _handle_admin_create_rag(event, user)
    elif len(rag_tail) == 1:
        # /admin/rag/{id}
        entry_id = rag_tail[0]
        if http_method == "PUT":
            return _handle_admin_update_rag(event, entry_id)
        elif http_method == "DELETE":
            return _handle_admin_delete_rag(entry_id)
        elif http_method == "GET":
            return _handle_admin_get_rag(entry_id)
    elif len(rag_tail) == 2:
        # /admin/rag/{id}/{action}
        entry_id, action = rag_tail[0], rag_tail[1]
        if action == "verify" and http_method == "POST":
            return _handle_admin_verify_rag(event, entry_id, user)
        elif action == "ai-review" and http_method == "POST":
            return _handle_admin_ai_review(entry_id)

    return cors_json_response(405, {"error": "Method not allowed"})


def _require_admin(event):
    """Returns (user, None) if admin, (None, error_response) otherwise."""
    user = _get_user_from_event(event)
    if not user:
        return None, cors_json_response(401, {"error": "Unauthorized. Please log in."})
    if not user.get("is_admin"):
        return None, cors_json_response(403, {"error": "Admin access required."})
    return user, None


def _parse_rag_key(entry_id: str) -> tuple:
    """Parse entry_id (format: scheme_id~section_id) into DynamoDB key. Handles legacy UUID-only ids."""
    if "~" in entry_id:
        scheme_id, section_id = entry_id.split("~", 1)
        return scheme_id, section_id
    return entry_id, "admin"


def _handle_admin_list_rag(event):
    """GET /admin/rag — List all knowledge entries (paginated)."""
    params = event.get("queryStringParameters") or {}
    category_filter = params.get("category", "")
    verified_filter = params.get("verified", "")
    keyword = params.get("q", "").lower()
    limit = min(int(params.get("limit", 200)), 500)

    try:
        result = knowledge_table.scan(Limit=limit)
        items = result.get("Items", [])

        # Normalise: every item gets a composite id = scheme_id~section_id so the
        # frontend can round-trip it back for PUT/DELETE/verify/ai-review.
        for item in items:
            sid = item.get("scheme_id", "unknown")
            sec = item.get("section_id", "overview")
            item["id"] = f"{sid}~{sec}"
            item.pop("embedding", None)
            # Normalise title — seed data uses name_en/name_hi instead of title
            if not item.get("title"):
                item["title"] = item.get("name_en") or item.get("name_hi") or sid
            # Normalise helpline_numbers — seed data uses helpline (singular string)
            if not item.get("helpline_numbers") and item.get("helpline"):
                item["helpline_numbers"] = [str(item["helpline"])]

        # Apply filters
        if category_filter:
            items = [i for i in items if i.get("category", "") == category_filter]
        if verified_filter in ("true", "false"):
            want_verified = verified_filter == "true"
            items = [i for i in items if bool(i.get("verified")) == want_verified]
        if keyword:
            items = [
                i for i in items
                if keyword in (i.get("title", "") or i.get("name_en", "") or "").lower()
                or keyword in (i.get("text_en", "") or "").lower()
                or keyword in (i.get("text_hi", "") or "").lower()
                or keyword in (i.get("category", "") or "").lower()
            ]

        items.sort(key=lambda x: int(x.get("created_at", x.get("updated_at", 0)) or 0), reverse=True)

        return cors_json_response(200, {"items": items, "count": len(items)})
    except Exception as e:
        logger.error(f"Admin list RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to list entries"})


def _handle_admin_get_rag(entry_id):
    """GET /admin/rag/{id} — Get a single knowledge entry."""
    try:
        scheme_id, section_id = _parse_rag_key(entry_id)
        result = knowledge_table.get_item(Key={"scheme_id": scheme_id, "section_id": section_id})
        item = result.get("Item")
        if not item:
            return cors_json_response(404, {"error": "Entry not found"})
        item.pop("embedding", None)
        item["id"] = f"{item.get('scheme_id', scheme_id)}~{item.get('section_id', section_id)}"
        # Normalise title
        if not item.get("title"):
            item["title"] = item.get("name_en") or item.get("name_hi") or scheme_id
        if not item.get("helpline_numbers") and item.get("helpline"):
            item["helpline_numbers"] = [str(item["helpline"])]
        return cors_json_response(200, item)
    except Exception as e:
        logger.error(f"Admin get RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to get entry"})


def _handle_admin_create_rag(event, user):
    """POST /admin/rag — Create a new knowledge entry with embedding."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    title = (body.get("title") or "").strip()
    if not title:
        return cors_json_response(400, {"error": "title is required"})

    entry_id = str(uuid.uuid4())
    now = int(time.time())

    entry = {
        # DynamoDB keys matching vaaniseva-knowledge table schema
        "scheme_id": entry_id,
        "section_id": "admin",
        # Composite id so the frontend can PUT/DELETE/verify back to the right key
        "id": f"{entry_id}~admin",
        "category": body.get("category", "general"),
        "title": title,
        "text_hi": body.get("text_hi", ""),
        "text_mr": body.get("text_mr", ""),
        "text_ta": body.get("text_ta", ""),
        "text_en": body.get("text_en", ""),
        "helpline_numbers": body.get("helpline_numbers", []),
        "source_url": body.get("source_url", ""),
        "documents_required": body.get("documents_required", []),
        "verified": False,
        "verified_by": None,
        "verified_at": None,
        "ai_review_status": None,
        "ai_review_notes": None,
        "created_at": now,
        "updated_at": now,
    }

    try:
        knowledge_table.put_item(Item=entry)

        # Generate combined embedding and save to vectors_table
        embed_text = " ".join(filter(None, [entry["text_en"], entry["text_hi"]]))
        if embed_text.strip():
            try:
                embedding = get_embedding(embed_text)
                from decimal import Decimal
                vectors_table.put_item(Item={
                    "embedding_id": f"{entry_id}#admin#all",
                    "scheme_id": entry_id,
                    "section_id": "admin",
                    "language": "all",
                    "title": title,
                    "text_hi": entry["text_hi"],
                    "text_mr": entry["text_mr"],
                    "text_ta": entry["text_ta"],
                    "text_en": entry["text_en"],
                    "embedding": [Decimal(str(round(x, 8))) for x in embedding],
                    "category": entry["category"],
                })
            except Exception as emb_err:
                logger.warning(f"Embedding generation failed (non-fatal): {emb_err}")

        entry.pop("embedding", None)
        return cors_json_response(201, entry)
    except Exception as e:
        logger.error(f"Admin create RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to create entry"})


def _handle_admin_update_rag(event, entry_id):
    """PUT /admin/rag/{id} — Update a knowledge entry."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    allowed_fields = [
        "category", "title", "text_hi", "text_mr", "text_ta", "text_en",
        "helpline_numbers", "source_url", "documents_required",
    ]
    updates = {k: body[k] for k in allowed_fields if k in body}
    if not updates:
        return cors_json_response(400, {"error": "No valid fields to update"})

    scheme_id, section_id = _parse_rag_key(entry_id)
    updates["updated_at"] = int(time.time())

    try:
        expr_parts, expr_vals, expr_names = [], {}, {}
        for i, (k, v) in enumerate(updates.items()):
            an, av = f"#f{i}", f":v{i}"
            expr_parts.append(f"{an} = {av}")
            expr_names[an] = k
            expr_vals[av] = v

        knowledge_table.update_item(
            Key={"scheme_id": scheme_id, "section_id": section_id},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_vals,
        )

        # Re-generate embedding if text was updated
        if any(f in updates for f in ("text_en", "text_hi", "text_mr", "text_ta")):
            try:
                full = knowledge_table.get_item(
                    Key={"scheme_id": scheme_id, "section_id": section_id}
                ).get("Item", {})
                embed_text = " ".join(filter(None, [full.get("text_en", ""), full.get("text_hi", "")]))
                if embed_text.strip():
                    from decimal import Decimal
                    embedding = get_embedding(embed_text)
                    emb_key = f"{scheme_id}#{section_id}#all"
                    vectors_table.update_item(
                        Key={"embedding_id": emb_key},
                        UpdateExpression="SET embedding = :emb, text_hi = :hi, text_mr = :mr, text_ta = :ta, text_en = :en",
                        ExpressionAttributeValues={
                            ":emb": [Decimal(str(round(x, 8))) for x in embedding],
                            ":hi": full.get("text_hi", ""),
                            ":mr": full.get("text_mr", ""),
                            ":ta": full.get("text_ta", ""),
                            ":en": full.get("text_en", ""),
                        },
                    )
            except Exception as emb_err:
                logger.warning(f"Embedding re-gen failed (non-fatal): {emb_err}")

        result = knowledge_table.get_item(Key={"scheme_id": scheme_id, "section_id": section_id})
        item = result.get("Item", {})
        item.pop("embedding", None)
        item["id"] = f"{scheme_id}~{section_id}"
        return cors_json_response(200, item)
    except Exception as e:
        logger.error(f"Admin update RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to update entry"})


def _handle_admin_delete_rag(entry_id):
    """DELETE /admin/rag/{id} — Delete a knowledge entry."""
    scheme_id, section_id = _parse_rag_key(entry_id)
    try:
        knowledge_table.delete_item(Key={"scheme_id": scheme_id, "section_id": section_id})
        try:
            vectors_table.delete_item(Key={"embedding_id": f"{scheme_id}#{section_id}#all"})
        except Exception:
            pass
        return cors_json_response(200, {"message": "Entry deleted", "id": entry_id})
    except Exception as e:
        logger.error(f"Admin delete RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to delete entry"})


def _handle_admin_verify_rag(event, entry_id, user):
    """POST /admin/rag/{id}/verify — Mark entry as verified."""
    scheme_id, section_id = _parse_rag_key(entry_id)
    try:
        now = int(time.time())
        knowledge_table.update_item(
            Key={"scheme_id": scheme_id, "section_id": section_id},
            UpdateExpression="SET verified = :v, verified_by = :vb, verified_at = :va, updated_at = :ua",
            ExpressionAttributeValues={
                ":v": True,
                ":vb": user.get("email", user.get("user_id", "unknown")),
                ":va": now,
                ":ua": now,
            },
        )
        return cors_json_response(200, {
            "message": "Entry verified",
            "id": entry_id,
            "verified_by": user.get("email"),
            "verified_at": now,
        })
    except Exception as e:
        logger.error(f"Admin verify RAG error: {e}")
        return cors_json_response(500, {"error": "Failed to verify entry"})


def _handle_admin_ai_review(entry_id):
    """POST /admin/rag/{id}/ai-review — AI fact-check via Bedrock."""
    try:
        scheme_id, section_id = _parse_rag_key(entry_id)
        result = knowledge_table.get_item(Key={"scheme_id": scheme_id, "section_id": section_id})
        item = result.get("Item")

        if not item:
            return cors_json_response(404, {"error": "Entry not found"})

        text_hi = item.get("text_hi", "")
        text_en = item.get("text_en", "")
        title = item.get("title") or item.get("name_en", "")
        helplines = item.get("helpline_numbers") or ([item["helpline"]] if item.get("helpline") else [])

        review_prompt = f"""You are a fact-checking agent for VaaniSeva, a voice AI for rural India.

Review this knowledge base entry and check:
1. Are phone numbers real and currently active Indian government numbers?
2. Are eligibility criteria consistent with official govt website text?
3. Are benefit amounts correct (cross-check your training data)?
4. Is any information potentially harmful or dangerously wrong?

Entry Title: {title}
Helpline Numbers: {', '.join(str(h) for h in helplines) if helplines else 'None'}
English Text: {text_en[:800]}
Hindi Text: {text_hi[:800]}

Return ONLY valid JSON (no markdown): {{"status": "PASS", "issues": [], "confidence": 0.9}}
Status must be one of: PASS, FLAG, FAIL
- PASS: Information appears accurate and safe
- FLAG: Minor issues or verify manually
- FAIL: Serious errors, dangerous misinformation, or fake phone numbers"""

        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": review_prompt}]}],
                "inferenceConfig": {"maxTokens": 400, "temperature": 0.1},
            }),
            contentType="application/json",
            accept="application/json",
        )
        raw = json.loads(response["body"].read())
        review_text = raw["output"]["message"]["content"][0]["text"].strip()

        review_text = re.sub(r"```[a-z]*", "", review_text).strip().strip("`")
        try:
            review_json = json.loads(review_text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', review_text, re.DOTALL)
            if match:
                review_json = json.loads(match.group())
            else:
                review_json = {"status": "FLAG", "issues": ["Could not parse AI review"], "confidence": 0.5}

        status = review_json.get("status", "FLAG")
        notes = "; ".join(review_json.get("issues", []))
        now = int(time.time())

        knowledge_table.update_item(
            Key={"scheme_id": scheme_id, "section_id": section_id},
            UpdateExpression="SET ai_review_status = :s, ai_review_notes = :n, updated_at = :ua",
            ExpressionAttributeValues={":s": status, ":n": notes, ":ua": now},
        )

        return cors_json_response(200, {
            "id": entry_id,
            "ai_review_status": status,
            "ai_review_notes": notes,
            "confidence": review_json.get("confidence", 0.5),
            "issues": review_json.get("issues", []),
        })
    except Exception as e:
        logger.error(f"Admin AI review error: {e}")
        return cors_json_response(500, {"error": "AI review failed"})


# ══════════════════════════════════════════════════════════════
#  Auth helpers — simple JWT-based auth with DynamoDB users table
# ══════════════════════════════════════════════════════════════

def _hash_password(password: str, salt: str = None) -> tuple:
    """Hash password with PBKDF2-HMAC-SHA256. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = os.urandom(32).hex()
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return h.hex(), salt


def _create_token(user_id: str, email: str) -> str:
    """Create a signed JWT token (or HMAC fallback)."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 7,  # 7 days
    }
    if _JWT_AVAILABLE:
        return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")
    # Simple HMAC fallback
    token_data = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    sig = hmac.new(JWT_SECRET.encode(), token_data.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{token_data}.{sig}".encode()).decode()


def _verify_token(token: str) -> dict | None:
    """Verify JWT and return payload, or None if invalid."""
    if not token:
        return None
    try:
        if _JWT_AVAILABLE:
            return pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        # HMAC fallback
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        data_str, sig = decoded.rsplit(".", 1)
        expected = hmac.new(JWT_SECRET.encode(), data_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(data_str)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def _get_user_from_event(event) -> dict | None:
    """Extract and verify user from Authorization header."""
    headers = event.get("headers", {}) or {}
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    token = auth.replace("Bearer ", "").strip()
    payload = _verify_token(token)
    if not payload:
        return None
    try:
        result = users_table.get_item(Key={"user_id": payload["sub"]})
        return result.get("Item")
    except Exception as e:
        logger.warning(f"Failed to fetch user: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  Auth routes — /auth/register, /auth/login
# ══════════════════════════════════════════════════════════════

def handle_auth_routes(event, path):
    """Route /auth/* requests."""
    if "/auth/register" in path:
        return _handle_register(event)
    elif "/auth/login" in path:
        return _handle_login(event)
    return cors_json_response(404, {"error": "Not found"})


def _handle_register(event):
    """POST /auth/register — Create a new user account."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    phone = (body.get("phone") or "").strip()

    if not name or not email or not password:
        return cors_json_response(400, {"error": "Name, email, and password are required."})

    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return cors_json_response(400, {"error": "Invalid email format."})

    if len(password) < 6:
        return cors_json_response(400, {"error": "Password must be at least 6 characters."})

    # Check if email already exists (scan — fine for hackathon scale)
    try:
        existing = users_table.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email},
            Limit=1,
        )
        if existing.get("Items"):
            return cors_json_response(409, {"error": "An account with this email already exists."})
    except Exception as e:
        logger.error(f"DynamoDB scan error: {e}")

    user_id = str(uuid.uuid4())
    pw_hash, salt = _hash_password(password)
    now = int(time.time())

    user_item = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "phone": phone,
        "pw_hash": pw_hash,
        "pw_salt": salt,
        "created_at": now,
        "updated_at": now,
        "language": "hi",
        "occupation": "",
        "state": "",
        "district": "",
        "enrolled_schemes": "",
        "custom_context": "",
        "tier": "free",
        "calls_this_month": 0,
    }

    try:
        users_table.put_item(Item=user_item)
        logger.info(f"New user registered: {user_id} ({email})")
        return cors_json_response(201, {"message": "Account created successfully.", "user_id": user_id})
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return cors_json_response(500, {"error": "Failed to create account. Please try again."})


def _handle_login(event):
    """POST /auth/login — Authenticate and return JWT."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return cors_json_response(400, {"error": "Email and password are required."})

    # Look up user by email
    try:
        result = users_table.scan(
            FilterExpression="email = :e",
            ExpressionAttributeValues={":e": email},
            Limit=1,
        )
        items = result.get("Items", [])
        if not items:
            return cors_json_response(401, {"error": "Invalid email or password."})

        user = items[0]
        pw_hash, _ = _hash_password(password, user.get("pw_salt", ""))
        if pw_hash != user.get("pw_hash"):
            return cors_json_response(401, {"error": "Invalid email or password."})

        token = _create_token(user["user_id"], user["email"])
        logger.info(f"User logged in: {user['user_id']}")
        return cors_json_response(200, {
            "token": token,
            "user": {
                "user_id": user["user_id"],
                "name": user.get("name", ""),
                "email": user["email"],
            },
        })
    except Exception as e:
        logger.error(f"Login error: {e}")
        return cors_json_response(500, {"error": "Login failed. Please try again."})


# ══════════════════════════════════════════════════════════════
#  Profile routes — /profile, /profile/history
# ══════════════════════════════════════════════════════════════

def handle_profile_routes(event, path):
    """Route /profile* requests. All require auth."""
    user = _get_user_from_event(event)
    if not user:
        return cors_json_response(401, {"error": "Unauthorized. Please log in."})

    if "/profile/history" in path:
        return _handle_call_history(event, user)

    http_method = event.get("httpMethod", "GET")
    if http_method == "GET":
        return _handle_get_profile(user)
    elif http_method == "POST":
        return _handle_update_profile(event, user)

    return cors_json_response(405, {"error": "Method not allowed"})


def _handle_get_profile(user):
    """GET /profile — Return user profile (exclude sensitive fields)."""
    safe_fields = {
        "user_id": user.get("user_id"),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "phone": user.get("phone", ""),
        "language": user.get("language", "hi"),
        "occupation": user.get("occupation", ""),
        "state": user.get("state", ""),
        "district": user.get("district", ""),
        "enrolled_schemes": user.get("enrolled_schemes", ""),
        "custom_context": user.get("custom_context", ""),
        "tier": user.get("tier", "free"),
        "calls_this_month": int(user.get("calls_this_month", 0)),
        "created_at": int(user.get("created_at", 0)),
    }
    return cors_json_response(200, safe_fields)


def _handle_update_profile(event, user):
    """POST /profile — Update profile fields."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    # Allowed fields to update
    allowed = ["name", "phone", "language", "occupation", "state", "district",
               "enrolled_schemes", "custom_context"]
    updates = {}
    for key in allowed:
        if key in body:
            updates[key] = str(body[key]).strip()

    if not updates:
        return cors_json_response(400, {"error": "No valid fields to update."})

    updates["updated_at"] = int(time.time())

    try:
        expr_parts = []
        expr_values = {}
        expr_names = {}
        for i, (k, v) in enumerate(updates.items()):
            attr_name = f"#f{i}"
            attr_val = f":v{i}"
            expr_parts.append(f"{attr_name} = {attr_val}")
            expr_names[attr_name] = k
            expr_values[attr_val] = v

        users_table.update_item(
            Key={"user_id": user["user_id"]},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )

        # Fetch and return updated profile
        result = users_table.get_item(Key={"user_id": user["user_id"]})
        updated = result.get("Item", user)
        return _handle_get_profile(updated)
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        return cors_json_response(500, {"error": "Failed to update profile."})


def _handle_call_history(event, user):
    """GET /profile/history — Return user's call history."""
    phone = user.get("phone", "")
    if not phone:
        return cors_json_response(200, {"calls": []})

    try:
        # Search calls table for calls from this user's phone number
        result = calls_table.scan(
            FilterExpression="from_number = :ph",
            ExpressionAttributeValues={":ph": phone},
        )
        calls = sorted(result.get("Items", []), key=lambda x: x.get("timestamp", 0), reverse=True)[:20]

        history = []
        for call in calls:
            history.append({
                "call_id": call.get("call_id", ""),
                "timestamp": int(call.get("timestamp", 0)),
                "language": call.get("language", ""),
                "conversation": call.get("conversation_history", [])[:10],  # Last 10 turns
            })

        return cors_json_response(200, {"calls": history})
    except Exception as e:
        logger.error(f"Call history fetch error: {e}")
        return cors_json_response(500, {"error": "Failed to fetch call history."})


# ══════════════════════════════════════════════════════════════
#  Auto language detection helpers
# ══════════════════════════════════════════════════════════════

def _get_phone_profile(phone_number: str) -> dict | None:
    """Look up a caller's profile from phone_profiles table by phone hash."""
    if not phone_profiles_table or not phone_number or phone_number == "unknown":
        return None
    try:
        phone_hash = _hash_phone(phone_number)
        result = phone_profiles_table.get_item(Key={"phone_hash": phone_hash})
        return result.get("Item")
    except Exception as e:
        logger.warning(f"Phone profile lookup failed: {e}")
        return None


def detect_language_from_speech(speech_text: str) -> str:
    """Use Bedrock to detect the language of a short speech utterance."""
    if not speech_text or not speech_text.strip():
        return "hi"  # default to Hindi
    try:
        prompt = f"What language is this text in? Reply with exactly one word: hindi, marathi, tamil, or english. Text: {speech_text}"
        response = bedrock.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": "You are a language detection tool. Reply with exactly one word."}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.0}
        )
        detected = response["output"]["message"]["content"][0]["text"].strip().lower()
        lang_map = {"hindi": "hi", "marathi": "mr", "tamil": "ta", "english": "en"}
        return lang_map.get(detected, "hi")
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "hi"


def handle_language_detect(params):
    """Handle first speech utterance for language detection (first-time callers)."""
    call_sid    = params.get("CallSid", "")
    speech_text = params.get("SpeechResult", "")
    digit       = params.get("Digits", "")
    from_number = params.get("From", "unknown")

    # If user pressed a digit instead of speaking, use DTMF mapping
    if digit and digit in DIGIT_TO_LANG:
        language = DIGIT_TO_LANG[digit]
    elif speech_text:
        language = detect_language_from_speech(speech_text)
    else:
        language = "hi"

    # Store detected language in phone_profiles
    if phone_profiles_table and from_number and from_number != "unknown":
        phone_hash = _hash_phone(from_number)
        try:
            phone_profiles_table.put_item(
                Item={
                    "phone_hash": phone_hash,
                    "language": language,
                    "preferred_agent": DEFAULT_AGENT,
                    "last_call_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "call_count": 1,
                },
                ConditionExpression="attribute_not_exists(phone_hash)"
            )
        except Exception as e:
            # Item may already exist — update language only
            try:
                phone_profiles_table.update_item(
                    Key={"phone_hash": phone_hash},
                    UpdateExpression="SET #lang = :lang",
                    ExpressionAttributeNames={"#lang": "language"},
                    ExpressionAttributeValues={":lang": language}
                )
            except Exception:
                pass

    # Update call record with detected language
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

    # Now go straight to gather with detected language + default agent
    agent = DEFAULT_AGENT
    agent_cfg = AGENT_REGISTRY[agent]
    agent_voice = agent_cfg["sarvam_speaker"]
    greeting_key = f"greeting_{language}"
    greeting = agent_cfg.get(greeting_key, agent_cfg["greeting_hi"])

    cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
    gather_url = f"{BASE_URL}/voice/gather?lang={language}&voice={agent_voice}&agent={agent}" if BASE_URL else f"/voice/gather?lang={language}&voice={agent_voice}&agent={agent}"

    response = VoiceResponse()
    gather = Gather(
        input="speech", action=gather_url, method="POST",
        language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
    )
    tts_say(gather, greeting, language, speaker=agent_voice)
    response.append(gather)
    return twiml_response(response)


# ── Step 1: New call comes in ────────────────────────────────
def handle_incoming(params):
    call_sid    = params.get("CallSid", str(uuid.uuid4()))
    from_number = params.get("From", "unknown")
    lang_param  = params.get("lang", "").strip()  # Browser calls pre-select language
    voice_param = params.get("voice", "").strip()  # Browser calls pre-select voice

    # Look up registered user by phone number for personalization
    caller_profile = _lookup_user_by_phone(from_number)

    language = lang_param if (lang_param in LANG_CONFIG) else (
        caller_profile.get("language", "en") if caller_profile else "en"
    )

    # Save call to DynamoDB
    calls_table.put_item(Item={
        "call_id": call_sid,
        "timestamp": int(datetime.now().timestamp()),
        "from_number": from_number,
        "status": "in-progress",
        "language": language,
        "voice_speaker": voice_param if voice_param in VOICE_OPTIONS else "",
        "queries_count": 0,
        "conversation_history": [],
        "user_id": caller_profile.get("user_id", "") if caller_profile else "",
        "source": "browser" if lang_param else "phone",
    })

    # Browser call: skip language menu, go to voice select (or straight to gather if voice pre-set)
    if lang_param and lang_param in LANG_CONFIG:
        return _browser_call_welcome(call_sid, language, voice=voice_param)

    # ── Returning phone caller? Check phone_profiles for stored language ──
    phone_profile = _get_phone_profile(from_number)
    if phone_profile and phone_profile.get("language"):
        # Returning caller — skip language menu entirely
        stored_lang = phone_profile["language"]
        stored_agent = phone_profile.get("preferred_agent", DEFAULT_AGENT)
        stored_name = phone_profile.get("user_name", "")
        agent_cfg = AGENT_REGISTRY.get(stored_agent, AGENT_REGISTRY[DEFAULT_AGENT])
        agent_voice = agent_cfg["sarvam_speaker"]
        greeting_key = f"greeting_{stored_lang}"
        greeting = agent_cfg.get(greeting_key, agent_cfg["greeting_hi"])
        if stored_name:
            # Personalize greeting for returning callers
            greeting = f"नमस्ते {stored_name}! " + greeting if stored_lang == "hi" else greeting

        cfg = LANG_CONFIG.get(stored_lang, LANG_CONFIG["en"])
        gather_url = f"{BASE_URL}/voice/gather?lang={stored_lang}&voice={agent_voice}&agent={stored_agent}" if BASE_URL else f"/voice/gather?lang={stored_lang}&voice={agent_voice}&agent={stored_agent}"

        resp = VoiceResponse()
        gather = Gather(
            input="speech", action=gather_url, method="POST",
            language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
        )
        tts_say(gather, greeting, stored_lang, speaker=agent_voice)
        resp.append(gather)
        return twiml_response(resp)

    # ── First-time phone caller — TTS welcome + digit/speech gather for language detection ──
    response = VoiceResponse()
    detect_url = f"{BASE_URL}/voice/language-detect" if BASE_URL else "/voice/language-detect"
    gather = Gather(
        input="speech dtmf", action=detect_url, method="POST",
        timeout=10, num_digits=1,
        language="hi-IN",
        hints="hindi, marathi, tamil, english, हाँ, हिंदी, मराठी",
    )

    # Welcome in each language so every caller hears their own language
    tts_say(gather,
            "नमस्ते! वाणीसेवा में आपका स्वागत है। हिंदी के लिए 1 दबाएं।",
            "hi", speaker="arya")
    tts_say(gather,
            "नमस्कार! मराठीसाठी 2 दाबा।",
            "mr", speaker="arya")
    tts_say(gather,
            "வணக்கம்! தமிழுக்கு 3 அழுத்தவும்।",
            "ta", speaker="arya")
    tts_say(gather,
            "Welcome! Press 4 for English.",
            "en", speaker="vidya")
    response.append(gather)

    # No-input fallback — prompt again via TTS
    tts_say(response,
            "कोई इनपुट नहीं मिला। कृपया दोबारा कॉल करें और 1, 2, 3 या 4 दबाएं।",
            "hi", speaker="arya")

    return twiml_response(response)


def _browser_call_welcome(call_sid: str, language: str, voice: str = ""):
    """Skip DTMF menu for browser calls — go to voice select then gather."""
    if voice and voice in VOICE_OPTIONS:
        # Web pre-selected voice — skip voice menu, greet and go straight to gather
        greetings = {
            "hi": "नमस्ते! मैं वाणीसेवा हूँ, आपकी अपनी दीदी। बताइए, आज मैं आपकी किस बात में मदद करूँ?",
            "mr": "नमस्कार! मी वाणीसेवा, तुमची ताई. बोला, आज मी तुम्हाला कशात मदत करू?",
            "ta": "வணக்கம்! நான் வாணீசேவா, உங்கள் அக்கா. சொல்லுங்க, இன்று நான் எப்படி உதவ வேண்டும்?",
            "en": "Hello! I'm VaaniSeva, your friendly helper. Tell me, how can I help you today?",
        }
        fallbacks = {
            "hi": "अरे, आवाज़ नहीं आई। एक बार फिर से बोलिए ना?",
            "mr": "अरे, ऐकू आलं नाही. पुन्हा एकदा सांगा ना?",
            "ta": "கேட்கவில்லை. மறுபடியும் சொல்லுங்க?",
            "en": "Oh, I didn't catch that. Could you say that again?",
        }
        cfg        = LANG_CONFIG[language]
        gather_url = f"{BASE_URL}/voice/gather?lang={language}&voice={voice}" if BASE_URL else f"/voice/gather?lang={language}&voice={voice}"
        response = VoiceResponse()
        gather   = Gather(
            input="speech", action=gather_url, method="POST",
            language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
        )
        tts_say(gather, greetings.get(language, greetings["en"]), language, speaker=voice)
        response.append(gather)
        tts_say(response, fallbacks.get(language, fallbacks["en"]), language, speaker=voice)
        return twiml_response(response)

    # No voice pre-selected — show voice selection menu
    return _play_voice_select_menu(call_sid, language)


# ── Step 2: Language selected → go to voice selection ───────
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

    # After language, ask user to pick a voice
    return _play_voice_select_menu(call_sid, language)


def _play_voice_select_menu(call_sid: str, language: str):
    """Play the voice selection IVR menu (1=Arya, 2=Vidya, 3=Hitesh)."""
    prompts = {
        "hi": "अब आवाज़ चुनिए। आर्या के लिए 1 दबाएं, विद्या के लिए 2, और हितेश के लिए 3 दबाएं।",
        "mr": "आता आवाज निवडा. आर्यासाठी 1, विद्यासाठी 2, आणि हितेशसाठी 3 दाबा.",
        "ta": "இப்போது குரலை தேர்வு செய்யுங்கள். ஆர்யாவிற்கு 1, வித்யாவிற்கு 2, ஹிதேஷிற்கு 3 அழுத்துங்கள்.",
        "en": "Now choose a voice. Press 1 for Arya, 2 for Vidya, or 3 for Hitesh.",
    }
    voice_select_url = f"{BASE_URL}/voice/voice-select?lang={language}" if BASE_URL else f"/voice/voice-select?lang={language}"
    cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
    response = VoiceResponse()
    gather = Gather(num_digits=1, action=voice_select_url, method="POST", timeout=8)
    # Use default lang voice to announce menu
    gather.say(prompts.get(language, prompts["en"]), voice=cfg["polly_voice"])
    response.append(gather)
    # No digit pressed — default to arya
    response.redirect(f"{voice_select_url}&Digits=1", method="POST")
    return twiml_response(response)


# ── Step 2b: Voice selected ───────────────────────────────────
def handle_voice_select(params):
    call_sid = params.get("CallSid", "")
    language = params.get("lang", "hi")
    digit    = params.get("Digits", "1")
    voice    = DIGIT_TO_VOICE.get(digit, "arya")

    # Persist chosen voice on the call record
    def _update_voice():
        try:
            ts = get_call_timestamp(call_sid)
            calls_table.update_item(
                Key={"call_id": call_sid, "timestamp": ts},
                UpdateExpression="SET voice_speaker = :v",
                ExpressionAttributeValues={":v": voice}
            )
        except Exception as e:
            logger.warning(f"DynamoDB voice update failed: {e}")
    threading.Thread(target=_update_voice, daemon=True).start()

    confirmations = {
        "hi":   {"arya": "ठीक है! आर्या की आवाज़ में बात करेंगे। बताइए आपका सवाल!",
                 "vidya": "ठीक है! विद्या की आवाज़ में बात करेंगे। बताइए आपका सवाल!",
                 "hitesh": "ठीक है! हितेश की आवाज़ में बात करेंगे। बताइए आपका सवाल!"},
        "mr":   {"arya": "ठीक आहे! आर्याच्या आवाजात बोलू. बोला तुमचा प्रश्न!",
                 "vidya": "ठीक आहे! विद्याच्या आवाजात बोलू. बोला तुमचा प्रश्न!",
                 "hitesh": "ठीक आहे! हितेशच्या आवाजात बोलू. बोला तुमचा प्रश्न!"},
        "ta":   {"arya": "சரி! ஆர்யா குரலில் பேசுவோம். கேளுங்கள்!",
                 "vidya": "சரி! வித்யா குரலில் பேசுவோம். கேளுங்கள்!",
                 "hitesh": "சரி! ஹிதேஷ் குரலில் பேசுவோம். கேளுங்கள்!"},
        "en":   {"arya": "Got it! You'll hear Arya's voice. Go ahead, ask your question!",
                 "vidya": "Got it! You'll hear Vidya's voice. Go ahead, ask your question!",
                 "hitesh": "Got it! You'll hear Hitesh's voice. Go ahead, ask your question!"},
    }
    fallbacks = {
        "hi": "कुछ सुनाई नहीं दिया। दोबारा कॉल करके बात कीजिए ना।",
        "mr": "काही ऐकू आलं नाही. पुन्हा कॉल करा ना.",
        "ta": "எதுவும் கேட்கவில்லை. மீண்டும் அழைக்கவும்.",
        "en": "I couldn't hear you. Please try calling again.",
    }

    cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
    confirmation = confirmations.get(language, confirmations["en"]).get(voice, "Let's go! Ask your question.")
    gather_url   = f"{BASE_URL}/voice/gather?lang={language}&voice={voice}" if BASE_URL else f"/voice/gather?lang={language}&voice={voice}"

    response = VoiceResponse()
    gather   = Gather(
        input="speech",
        action=gather_url,
        method="POST",
        language=cfg["twilio_speech_lang"],
        speech_timeout="auto",
        timeout=10
    )
    tts_say(gather, confirmation, language, speaker=voice)
    response.append(gather)
    tts_say(response, fallbacks.get(language, fallbacks["en"]), language, speaker=voice)
    return twiml_response(response)


def _get_call_voice(call_sid: str, fallback_voice: str = "arya") -> str:
    """Read the caller's chosen voice from DynamoDB."""
    try:
        ts = get_call_timestamp(call_sid)
        item = calls_table.get_item(Key={"call_id": call_sid, "timestamp": ts}).get("Item", {})
        return item.get("voice_speaker", fallback_voice)
    except Exception:
        return fallback_voice


# ── Step 3: User spoke — kick off async processing ──────────
def handle_gather(params):
    """
    Immediately responds with a "please wait" message and redirects to
    /voice/poll, while processing RAG + TTS in a background thread.
    This eliminates the silent wait the user previously experienced.
    """
    call_sid    = params.get("CallSid", "")
    speech_text = params.get("SpeechResult", "")
    language    = params.get("lang", "hi")
    voice       = params.get("voice", "") or _get_call_voice(call_sid)
    current_agent = params.get("agent", "")

    logger.info(f"Speech: '{speech_text}' | Lang: {language} | Voice: {voice} | Agent: {current_agent} | Call: {call_sid}")

    # ── Goodbye detection — end the call immediately ──────────────
    bye_triggers = [
        "bye", "goodbye", "alvida", "अलविदा", "band karo", "बंद करो",
        "rakh do", "रख दो", "phone rakh", "फोन रख", "bas", "बस",
        "shukriya bye", "शुक्रिया बाय", "thank you bye", "cut the call",
        "call end", "phone band", "விடை", "போதும்"
    ]
    if speech_text and any(t in speech_text.lower() for t in bye_triggers):
        goodbyes = {
            "hi": "अच्छा चलिए, ख्याल रखिए! फिर कभी कॉल कीजिए।",
            "mr": "बरं चला, काळजी घ्या! पुन्हा कॉल करा.",
            "ta": "சரி, கவனமா இருங்க! மீண்டும் அழையுங்க.",
            "en": "Take care! Call again anytime.",
        }
        response = VoiceResponse()
        tts_say(response, goodbyes.get(language, goodbyes["en"]), language, speaker=voice)
        response.hangup()
        return twiml_response(response)

    # Mid-call voice switch: user says "change voice" / "आवाज़ बदलो" etc.
    change_triggers = ["change voice", "change my voice", "different voice",
                       "आवाज़ बदलो", "आवाज बदलो", "दूसरी आवाज़",
                       "आवाज बदल", "voice change", "குரல் மாற்று", "आवाज बदलवा"]
    if speech_text and any(t in speech_text.lower() for t in change_triggers):
        return _play_voice_select_menu(call_sid, language)

    if not speech_text:
        return ask_again(language)

    # ── Detect or maintain current agent ───────────────────────────
    if not current_agent:
        current_agent = detect_agent_from_intent(speech_text, language)
    else:
        # Check for mid-call agent switch request
        requested_agent = detect_agent_from_intent(speech_text, language)
        if requested_agent != current_agent:
            # Switch if user explicitly named an agent (check name triggers)
            name_triggers = {"arya": ["arya", "आर्या"], "hitesh": ["hitesh", "हितेश"], "vidya": ["vidya", "विद्या"]}
            text_lower = speech_text.lower()
            explicitly_named = any(t in text_lower for t in name_triggers.get(requested_agent, []))
            if explicitly_named:
                # Play transfer announcement in CURRENT agent's voice
                old_agent_cfg = AGENT_REGISTRY.get(current_agent, AGENT_REGISTRY[DEFAULT_AGENT])
                old_voice = old_agent_cfg["sarvam_speaker"]
                transfer_msgs = {
                    "hi": f"ठीक है, मैं आपको {AGENT_REGISTRY[requested_agent]['name_hi']} से जोड़ रही हूँ। एक सेकंड।",
                    "mr": f"ठीक आहे, मी तुम्हाला {AGENT_REGISTRY[requested_agent]['name']} शी जोडतो. एक क्षण.",
                    "ta": f"சரி, உங்களை {AGENT_REGISTRY[requested_agent]['name']} கிட்ட இணைக்கிறேன். ஒரு நிமிஷம்.",
                    "en": f"Sure, let me connect you to {AGENT_REGISTRY[requested_agent]['name']}. One moment.",
                }
                current_agent = requested_agent
                agent_cfg = AGENT_REGISTRY[current_agent]
                greeting_key = f"greeting_{language}"
                switch_msg = agent_cfg.get(greeting_key, agent_cfg["greeting_hi"])
                agent_voice = agent_cfg["sarvam_speaker"]
                cfg = LANG_CONFIG.get(language, LANG_CONFIG["en"])
                gather_url = f"{BASE_URL}/voice/gather?lang={language}&voice={agent_voice}&agent={current_agent}" if BASE_URL else f"/voice/gather?lang={language}&voice={agent_voice}&agent={current_agent}"
                response = VoiceResponse()
                # Transfer announcement in old agent's voice
                tts_say(response, transfer_msgs.get(language, transfer_msgs["hi"]), language, speaker=old_voice)
                response.pause(length=1)
                # New agent greeting in new agent's voice
                gather = Gather(
                    input="speech", action=gather_url, method="POST",
                    language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
                )
                tts_say(gather, switch_msg, language, speaker=agent_voice)
                response.append(gather)
                return twiml_response(response)

    # Use agent's voice for TTS if no explicit voice override was chosen
    agent_voice = AGENT_REGISTRY.get(current_agent, AGENT_REGISTRY[DEFAULT_AGENT])["sarvam_speaker"]
    if not params.get("voice"):
        voice = agent_voice

    job_key = f"job#{call_sid}"

    # ── Write "processing" sentinel so poll knows a job is active ──
    try:
        calls_table.put_item(Item={
            "call_id": job_key,
            "timestamp": 0,
            "status": "processing",
            "lang": language,
            "voice": voice,
            "ttl": int(time.time()) + 300,  # auto-expire in 5 min
        })
    except Exception as e:
        logger.warning(f"Job sentinel write failed (non-fatal): {e}")

    # ── Background thread: two-phase LLM → store result in DynamoDB ──
    def _process_async():
        try:
            profile_context = ""
            cross_call_context = ""
            from_number = ""
            phone_hash = ""

            def _fetch_profile():
                """Fetch caller profile and cross-call context."""
                _prof = ""
                _cross = ""
                _from = ""
                _phash = ""
                try:
                    ts = get_call_timestamp(call_sid)
                    call_item = calls_table.get_item(Key={"call_id": call_sid, "timestamp": ts}).get("Item", {})
                    _from = call_item.get("from_number", "")
                    user_id = call_item.get("user_id", "")
                    if user_id:
                        user_result = users_table.get_item(Key={"user_id": user_id})
                        caller = user_result.get("Item")
                        if caller:
                            _prof = _build_profile_context(caller)
                    if _from and _from != "unknown":
                        _phash = _hash_phone(_from)
                        phone_prof = _get_phone_profile(_from)
                        if phone_prof and phone_prof.get("last_topic"):
                            _cross = phone_prof["last_topic"]
                except Exception as pe:
                    logger.warning(f"Profile lookup for call {call_sid}: {pe}")
                return _prof, _cross, _from, _phash

            def _fetch_history():
                """Fetch conversation history for this call."""
                return get_conversation_history(call_sid) if call_sid else []

            # ── Phase 1: Fast LLM (profile + history only, NO RAG/data.gov) ──
            with ThreadPoolExecutor(max_workers=2) as executor:
                fut_profile = executor.submit(_fetch_profile)
                fut_hist    = executor.submit(_fetch_history)
                profile_context, cross_call_context, from_number, phone_hash = fut_profile.result()
                history = fut_hist.result()

            call_system_prompt = build_system_prompt(
                current_agent, language,
                user_name=None,
                cross_call_context=cross_call_context
            )

            quick_answer = ask_llm(speech_text, "", language, history,
                                   profile_context=profile_context,
                                   system_prompt=call_system_prompt)

            needs_data = "[FETCH_DATA]" in quick_answer
            clean_answer = quick_answer.replace("[FETCH_DATA]", "").strip()

            if not needs_data:
                # ── Simple query — TTS and done (fast path ~5-6s) ──
                import re as _re
                sentence_split = _re.split(r'(?<=[।\.!\?])', clean_answer, maxsplit=1)
                first_sentence = sentence_split[0].strip()
                remainder = sentence_split[1].strip() if len(sentence_split) > 1 else ""

                first_audio = sarvam_tts(first_sentence, language, speaker=voice) or ""
                rest_audio = ""
                if remainder:
                    rest_audio = sarvam_tts(remainder, language, speaker=voice) or ""

                calls_table.put_item(Item={
                    "call_id": job_key,
                    "timestamp": 0,
                    "status": "done",
                    "answer": clean_answer,
                    "audio_url": first_audio,
                    "rest_audio_url": rest_audio,
                    "lang": language,
                    "ttl": int(time.time()) + 300,
                })
                log_query(call_sid, speech_text, clean_answer, language)
                logger.info(f"Fast path done for call={call_sid}")
            else:
                # ── Data needed — serve acknowledgment, then fetch ──
                ack_audio = sarvam_tts(clean_answer, language, speaker=voice) or ""
                calls_table.put_item(Item={
                    "call_id": job_key,
                    "timestamp": 0,
                    "status": "partial",
                    "answer": clean_answer,
                    "audio_url": ack_audio,
                    "lang": language,
                    "ttl": int(time.time()) + 300,
                })
                logger.info(f"Partial (ack) served for call={call_sid}, fetching data...")

                # ── Phase 2: Fetch RAG + data.gov in parallel ──
                def _fetch_rag_context():
                    use_rag = should_use_rag(speech_text)
                    if not use_rag:
                        return ""
                    embedding = get_embedding(speech_text)
                    return retrieve_context(embedding, language)

                def _fetch_live_data():
                    if not DATA_GOV_API_KEY:
                        return ""
                    return _fetch_data_gov(speech_text)

                with ThreadPoolExecutor(max_workers=2) as executor:
                    fut_rag  = executor.submit(_fetch_rag_context)
                    fut_live = executor.submit(_fetch_live_data)
                    rag_context = fut_rag.result()
                    live_data   = fut_live.result()

                context = rag_context
                if live_data:
                    context = f"{context}\n\n--- Live Government Data (data.gov.in) ---\n{live_data}"

                # Phase 2 LLM: now with full context
                data_answer = ask_llm(speech_text, context, language, history,
                                      profile_context=profile_context,
                                      system_prompt=call_system_prompt)
                # Strip any accidental [FETCH_DATA] from Phase 2
                data_answer = data_answer.replace("[FETCH_DATA]", "").strip()

                import re as _re
                sentence_split = _re.split(r'(?<=[।\.!\?])', data_answer, maxsplit=1)
                first_sentence = sentence_split[0].strip()
                remainder = sentence_split[1].strip() if len(sentence_split) > 1 else ""

                first_audio = sarvam_tts(first_sentence, language, speaker=voice) or ""
                rest_audio = ""
                if remainder:
                    rest_audio = sarvam_tts(remainder, language, speaker=voice) or ""

                calls_table.put_item(Item={
                    "call_id": job_key,
                    "timestamp": 0,
                    "status": "done",
                    "answer": data_answer,
                    "audio_url": first_audio,
                    "rest_audio_url": rest_audio,
                    "lang": language,
                    "ttl": int(time.time()) + 300,
                })
                log_query(call_sid, speech_text, data_answer, language)
                logger.info(f"Data path done for call={call_sid}")

            # Update cross-call memory (fire-and-forget)
            if phone_hash:
                try:
                    summarize_and_store_call(phone_hash, history, language, current_agent)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Async RAG error for call={call_sid}: {e}")
            try:
                calls_table.put_item(Item={
                    "call_id": job_key,
                    "timestamp": 0,
                    "status": "error",
                    "lang": language,
                    "ttl": int(time.time()) + 300,
                })
            except Exception:
                pass

    threading.Thread(target=_process_async, daemon=True).start()

    # ── Brief pause then poll (no filler — Phase 1 LLM answers fast) ──
    cfg      = LANG_CONFIG.get(language, LANG_CONFIG["en"])
    poll_url = f"{BASE_URL}/voice/poll?lang={language}&voice={voice}&agent={current_agent}" if BASE_URL else f"/voice/poll?lang={language}&voice={voice}&agent={current_agent}"

    response = VoiceResponse()
    response.pause(length=1)
    response.redirect(poll_url, method="POST")
    return twiml_response(response)


# ── Step 3b: Poll for async result ──────────────────────────
def handle_poll(params):
    """
    Called by Twilio after the "thinking" message plays.
    Polls DynamoDB until the background RAG job completes, then returns
    the TTS audio.  Allows up to two poll hops (~20 s total) before
    giving up gracefully.
    """
    call_sid = params.get("CallSid", "")
    language = params.get("lang", "hi")
    attempt  = int(params.get("attempt", "0"))
    voice    = params.get("voice", "") or _get_call_voice(call_sid)
    current_agent = params.get("agent", DEFAULT_AGENT)
    partial_played = params.get("pp", "0") == "1"  # was partial ack already played?

    job_key = f"job#{call_sid}"
    cfg     = LANG_CONFIG.get(language, LANG_CONFIG["en"])

    follow_ups = {
        "hi": "और बताइए, कुछ और जानना है?",
        "mr": "आणखी काही विचारायचं आहे का?",
        "ta": "வேறு ஏதாவது கேட்க வேண்டுமா?",
        "en": "Anything else you'd like to know?",
    }
    goodbyes = {
        "hi": "अच्छा चलिए, ख्याल रखिए! वाणीसेवा को कॉल करने के लिए शुक्रिया।",
        "mr": "बरं चला, काळजी घ्या! वाणीसेवाला कॉल केल्याबद्दल धन्यवाद.",
        "ta": "சரி, கவனமா இருங்க! வாணீசேவாவை அழைத்ததற்கு நன்றி.",
        "en": "Alright, take care! Thanks for calling VaaniSeva.",
    }
    error_msgs = {
        "hi": "माफ करें, अभी कुछ समस्या आ रही है। कृपया फिर से बोलें।",
        "mr": "क्षमस्व, आत्ता काही अडचण आहे. कृपया पुन्हा सांगा.",
        "ta": "மன்னிக்கவும், சிக்கல் ஏற்பட்டது. மீண்டும் பேசுங்கள்.",
        "en": "I'm sorry, I had trouble with that. Please ask your question again.",
    }

    gather_url = f"{BASE_URL}/voice/gather?lang={language}&voice={voice}&agent={current_agent}" if BASE_URL else f"/voice/gather?lang={language}&voice={voice}&agent={current_agent}"
    response   = VoiceResponse()

    # Poll DynamoDB every ~1.5 s for up to 10 s
    # If partial was already played, only wait for done/error
    acceptable = ("done", "error") if partial_played else ("done", "error", "partial")
    result   = None
    deadline = time.time() + 10.0
    while time.time() < deadline:
        try:
            item = calls_table.get_item(Key={"call_id": job_key, "timestamp": 0}).get("Item")
            if item and item.get("status") in acceptable:
                result = item
                break
        except Exception as e:
            logger.warning(f"Poll DynamoDB error: {e}")
        time.sleep(1.5)

    # ── Still processing after 10 s? ───────────────────────────────
    if result is None:
        if attempt < 1:
            # One more hop — play brief hold message, try again
            still_msgs = {
                "hi": "बस थोड़ी देर और, लगभग हो गया।",
                "mr": "आणखी थोडा वेळ, जवळजवळ झाले.",
                "ta": "இன்னும் கொஞ்சம் நேரம், கிட்டத்தட்ட முடிந்தது.",
                "en": "Almost there, just a few more seconds.",
            }
            pp_flag = "1" if partial_played else "0"
            response.pause(length=1)
            next_poll = (
                f"{BASE_URL}/voice/poll?lang={language}&attempt=1&voice={voice}&agent={current_agent}&pp={pp_flag}"
                if BASE_URL else f"/voice/poll?lang={language}&attempt=1&voice={voice}&agent={current_agent}&pp={pp_flag}"
            )
            response.redirect(next_poll, method="POST")
        else:
            # Give up after ~20 s total — let user ask again
            gather = Gather(
                input="speech", action=gather_url, method="POST",
                language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
            )
            gather.say(error_msgs.get(language, error_msgs["en"]), voice=cfg["polly_voice"])
            response.append(gather)
            response.say(goodbyes.get(language, goodbyes["en"]), voice=cfg["polly_voice"])
        return twiml_response(response)

    # ── Error result ────────────────────────────────────────────────
    if result.get("status") == "error":
        # Clean up job record
        threading.Thread(
            target=lambda: calls_table.delete_item(Key={"call_id": job_key, "timestamp": 0}),
            daemon=True,
        ).start()
        gather = Gather(
            input="speech", action=gather_url, method="POST",
            language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
        )
        gather.say(error_msgs.get(language, error_msgs["en"]), voice=cfg["polly_voice"])
        response.append(gather)
        response.say(goodbyes.get(language, goodbyes["en"]), voice=cfg["polly_voice"])
        return twiml_response(response)

    # ── Partial result (Phase 1 ack — play ONCE, then poll for done) ──
    if result.get("status") == "partial":
        ack_audio = result.get("audio_url", "")
        if ack_audio:
            response.play(ack_audio)
        else:
            ack_text = result.get("answer", "")
            if ack_text:
                response.say(ack_text, voice=cfg["polly_voice"])
        # Redirect to poll again but with pp=1 so we only wait for done/error
        next_poll = (
            f"{BASE_URL}/voice/poll?lang={language}&attempt=0&voice={voice}&agent={current_agent}&pp=1"
            if BASE_URL else f"/voice/poll?lang={language}&attempt=0&voice={voice}&agent={current_agent}&pp=1"
        )
        response.redirect(next_poll, method="POST")
        return twiml_response(response)

    # ── Success — play answer + prompt for next question ───────────
    # Clean up job record (fire-and-forget)
    threading.Thread(
        target=lambda: calls_table.delete_item(Key={"call_id": job_key, "timestamp": 0}),
        daemon=True,
    ).start()

    answer    = result.get("answer", "")
    # Truncate long responses — phone calls need brevity
    if len(answer) > 500:
        answer = answer[:500].rsplit(' ', 1)[0] + "..."
    # Use the voice stored in the job record (ensures consistency even on retry hops)
    stored_voice = result.get("voice", voice)
    audio_url = result.get("audio_url", "")
    follow_up = follow_ups.get(language, follow_ups["en"])
    goodbye   = goodbyes.get(language, goodbyes["en"])

    rest_audio_url = result.get("rest_audio_url", "")

    gather = Gather(
        input="speech", action=gather_url, method="POST",
        language=cfg["twilio_speech_lang"], speech_timeout="auto", timeout=15,
    )
    if audio_url:
        gather.play(audio_url)
        if rest_audio_url:
            gather.play(rest_audio_url)
        tts_say(gather, follow_up, language, speaker=stored_voice)
    else:
        # Sarvam TTS unavailable — retry once, then fall back to Polly
        retry_url = sarvam_tts(answer, language, speaker=stored_voice)
        if retry_url:
            gather.play(retry_url)
            tts_say(gather, follow_up, language, speaker=stored_voice)
        else:
            gather.say(answer, voice=cfg["polly_voice"])
            gather.say(follow_up, voice=cfg["polly_voice"])
    response.append(gather)
    tts_say(response, goodbye, language, speaker=stored_voice)
    return twiml_response(response)


# ── RAG Pipeline (with conversation memory) ──────────────────
def _build_profile_context(user: dict) -> str:
    """Build a profile context string to inject into LLM system prompt."""
    parts = []
    if user.get("name"):
        parts.append(f"User's name: {user['name']}")
    if user.get("occupation"):
        parts.append(f"Occupation: {user['occupation']}")
    if user.get("state"):
        parts.append(f"State: {user['state']}")
    if user.get("district"):
        parts.append(f"District: {user['district']}")
    if user.get("enrolled_schemes"):
        parts.append(f"Already enrolled in: {user['enrolled_schemes']}")
    if user.get("custom_context"):
        parts.append(f"Additional context: {user['custom_context']}")
    if user.get("language"):
        parts.append(f"Preferred language: {user['language']}")
    if not parts:
        return ""
    return "USER PROFILE (use this to personalize your response, address them by name):\n" + "\n".join(parts)


def _lookup_user_by_phone(phone: str) -> dict | None:
    """Look up a user by phone number."""
    if not phone:
        return None
    try:
        result = users_table.scan(
            FilterExpression="phone = :ph",
            ExpressionAttributeValues={":ph": phone},
            Limit=1,
        )
        items = result.get("Items", [])
        return items[0] if items else None
    except Exception as e:
        logger.warning(f"Phone lookup failed: {e}")
        return None


def _fetch_data_gov(query: str) -> str:
    """Fetch relevant data from data.gov.in APIs. Returns summary text or empty string."""
    if not DATA_GOV_API_KEY:
        return ""

    results = []

    # ── 1. Mandi / market price queries → Agmarknet daily prices API ──
    mandi_keywords = ["mandi", "मंडी", "bhav", "भाव", "price", "rate", "daam", "दाम",
                      "sabzi", "सब्जी", "vegetable", "tomato", "tamatar", "टमाटर",
                      "onion", "pyaaz", "प्याज", "potato", "aloo", "आलू", "wheat",
                      "gehu", "गेहूं", "rice", "chawal", "चावल", "market"]
    query_lower = query.lower()
    if any(kw in query_lower for kw in mandi_keywords):
        try:
            mandi_params = {
                "api-key": DATA_GOV_API_KEY,
                "format": "json",
                "limit": 5,
            }
            # Extract commodity from query
            commodity_map = {
                "tomato": "Tomato", "tamatar": "Tomato", "टमाटर": "Tomato",
                "onion": "Onion", "pyaaz": "Onion", "प्याज": "Onion",
                "potato": "Potato", "aloo": "Potato", "आलू": "Potato",
                "wheat": "Wheat", "gehu": "Wheat", "गेहूं": "Wheat",
                "rice": "Rice", "chawal": "Rice", "चावल": "Rice",
                "apple": "Apple", "seb": "Apple", "सेब": "Apple",
                "banana": "Banana", "kela": "Banana", "केला": "Banana",
                "dal": "Masur Dal", "दाल": "Masur Dal",
                "sugar": "Sugar", "cheeni": "Sugar", "चीनी": "Sugar",
                "soyabean": "Soyabean", "soybean": "Soyabean", "सोयाबीन": "Soyabean",
            }
            for keyword, commodity in commodity_map.items():
                if keyword in query_lower:
                    mandi_params["filters[commodity]"] = commodity
                    break

            # Extract state from query
            state_map = {
                "mp": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh", "मध्य प्रदेश": "Madhya Pradesh",
                "up": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh", "उत्तर प्रदेश": "Uttar Pradesh",
                "rajasthan": "Rajasthan", "राजस्थान": "Rajasthan",
                "bihar": "Bihar", "बिहार": "Bihar",
                "maharashtra": "Maharashtra", "महाराष्ट्र": "Maharashtra",
                "punjab": "Punjab", "पंजाब": "Punjab",
                "haryana": "Haryana", "हरियाणा": "Haryana",
                "gujarat": "Gujarat", "गुजरात": "Gujarat",
                "karnataka": "Karnataka", "कर्नाटक": "Karnataka",
                "tamil nadu": "Tamil Nadu", "तमिलनाडु": "Tamil Nadu",
                "andhra pradesh": "Andhra Pradesh", "आंध्र प्रदेश": "Andhra Pradesh",
                "telangana": "Telangana", "तेलंगाना": "Telangana",
                "west bengal": "West Bengal", "पश्चिम बंगाल": "West Bengal",
                "odisha": "Odisha", "ओडिशा": "Odisha",
                "chhattisgarh": "Chhattisgarh", "छत्तीसगढ़": "Chhattisgarh",
                "jharkhand": "Jharkhand", "झारखंड": "Jharkhand",
                "assam": "Assam", "असम": "Assam",
                "kerala": "Kerala", "केरल": "Kerala",
                "goa": "Goa", "गोवा": "Goa",
            }
            for keyword, state_name in state_map.items():
                if keyword in query_lower:
                    mandi_params["filters[state]"] = state_name
                    break

            resp = requests.get(
                "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
                params=mandi_params,
                timeout=4,
            )
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("records", [])
                if records:
                    price_lines = []
                    for rec in records[:5]:
                        commodity = rec.get("commodity", "")
                        market = rec.get("market", "")
                        state = rec.get("state", "")
                        modal_price = rec.get("modal_price", "")
                        arrival_date = rec.get("arrival_date", "")
                        if commodity and modal_price:
                            price_lines.append(
                                f"{commodity} in {market}, {state}: Rs {modal_price}/quintal (date: {arrival_date})"
                            )
                    if price_lines:
                        results.append("LIVE MANDI PRICES:\n" + "\n".join(price_lines))
                else:
                    results.append("No mandi price data found for this query. The data might not be available for the requested commodity or state right now.")
            else:
                logger.warning(f"Mandi API returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"Mandi price fetch failed: {e}")

    return "\n".join(results)


def should_use_rag(speech_text: str) -> bool:
    """Decide whether RAG retrieval is needed for this utterance."""
    text_lower = speech_text.lower().strip()

    # Skip RAG: conversational/follow-up utterances
    skip_keywords = [
        "theek", "ठीक", "samajh", "समझ", "aur batao", "और बताओ",
        "haan", "हाँ", "ok", "accha", "अच्छा", "shukriya", "शुक्रिया",
        "bye", "band karo", "thanks", "nahi", "नहीं"
    ]
    if any(kw in text_lower for kw in skip_keywords):
        return False

    # Skip RAG: live data queries (handled by API tools)
    live_keywords = [
        "mandi", "मंडी", "bhav", "भाव", "price", "rate", "bhaav",
        "mausam", "मौसम", "barish", "बारिश", "weather", "temperature"
    ]
    if any(kw in text_lower for kw in live_keywords):
        return False

    # Skip RAG: very short utterances (under 4 words = conversational)
    if len(speech_text.split()) < 4:
        return False

    return True  # default: use RAG


def rag_pipeline(query: str, language: str, call_sid: str = "", profile_context: str = "", system_prompt: str = "") -> str:
    use_rag = should_use_rag(query)
    context = ""
    if use_rag:
        embedding = get_embedding(query)
        context   = retrieve_context(embedding, language)

    # Augment context with live data.gov.in data if API key is set
    live_data = _fetch_data_gov(query) if DATA_GOV_API_KEY else ""
    if live_data:
        context = f"{context}\n\n--- Live Government Data (data.gov.in) ---\n{live_data}"

    history   = get_conversation_history(call_sid) if call_sid else []
    return ask_llm(query, context, language, history, profile_context=profile_context, system_prompt=system_prompt)


def get_conversation_history(call_sid: str) -> list:
    """Fetch conversation history from DynamoDB for this call."""
    if not call_sid:
        return []
    try:
        ts = get_call_timestamp(call_sid)
        result = calls_table.get_item(Key={"call_id": call_sid, "timestamp": ts})
        item = result.get("Item", {})
        return item.get("conversation_history", [])
    except Exception as e:
        logger.warning(f"Failed to fetch conversation history: {e}")
        return []


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


def ask_llm(query: str, context: str, language: str, history: list = None, profile_context: str = "", system_prompt: str = "") -> str:
    lang_instructions = {
        "hi": "LANGUAGE: Hindi ONLY. हिंदी देवनागरी लिपि में जवाब दो। कोई अंग्रेजी/रोमन अक्षर नहीं। सिर्फ proper nouns (PM-Kisan, Ayushman Bharat) अंग्रेजी में रख सकती हो।",
        "mr": "LANGUAGE: Marathi ONLY. उत्तर फक्त मराठी लिपीत द्या. हिंदी मिसळू नका. फक्त proper nouns (PM-Kisan, Ayushman Bharat) इंग्रजीत ठेवा.",
        "ta": "LANGUAGE: Tamil ONLY. பதிலை முழுவதுமாக தமிழில் கொடுங்கள். ஆங்கிலம் வேண்டாம். proper nouns (PM-Kisan, Ayushman Bharat) மட்டும் ஆங்கிலத்தில்.",
        "en": "LANGUAGE: English ONLY. Respond in simple, clear English. No Hindi or other scripts.",
    }
    lang_instruction = lang_instructions.get(language, lang_instructions["en"])

    # Build user message with optional profile context
    profile_section = f"\n\n{profile_context}\n" if profile_context else ""

    user_msg = f"""[{lang_instruction}]
{profile_section}
Relevant context from our knowledge base (use if helpful, ignore if not relevant):
{context}

User: {query}"""

    # Resolve system prompt — fall back to default agent if not provided
    resolved_prompt = system_prompt or build_system_prompt(DEFAULT_AGENT, language)

    # Try OpenAI first if configured
    if LLM_PROVIDER == "openai" and openai_client:
        try:
            return _ask_openai(user_msg, history or [], system_prompt=resolved_prompt)
        except Exception as e:
            logger.warning(f"OpenAI failed, falling back to Bedrock: {e}")

    # Bedrock (primary)
    return _ask_bedrock(user_msg, history or [], system_prompt=resolved_prompt)


def _ask_openai(user_msg: str, history: list, system_prompt: str = "") -> str:
    """Call OpenAI GPT-4o-mini with full conversation history."""
    messages = [{"role": "system", "content": system_prompt or build_system_prompt(DEFAULT_AGENT, "hi")}]

    # Add conversation history (last 10 turns max to stay within context)
    for turn in (history or [])[-10:]:
        messages.append({"role": "user", "content": turn.get("query", "")})
        messages.append({"role": "assistant", "content": turn.get("answer", "")})

    # Current user message
    messages.append({"role": "user", "content": user_msg})

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def _ask_bedrock(user_msg: str, history: list = None, system_prompt: str = "") -> str:
    """Call Bedrock via Converse API with system prompt and conversation history."""
    messages = []

    # Add conversation history (last 10 turns)
    for turn in (history or [])[-10:]:
        if turn.get("query"):
            messages.append({"role": "user", "content": [{"text": turn["query"]}]})
        if turn.get("answer"):
            messages.append({"role": "assistant", "content": [{"text": turn["answer"]}]})

    # Current user message
    messages.append({"role": "user", "content": [{"text": user_msg}]})

    response = bedrock.converse(
        modelId=BEDROCK_MODEL_ID,
        system=[{"text": system_prompt or build_system_prompt(DEFAULT_AGENT, "hi")}],
        messages=messages,
        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.7,
        }
    )
    return response["output"]["message"]["content"][0]["text"].strip()


# ══════════════════════════════════════════════════════════════
#  Cross-call memory — summarize & store after each call
# ══════════════════════════════════════════════════════════════

def call_bedrock_simple(prompt: str, max_tokens: int = 60) -> str:
    """Simple Bedrock call for utility tasks (summaries, detection, etc.)."""
    try:
        response = bedrock.converse(
            modelId=BEDROCK_MODEL_ID,
            system=[{"text": "You are a concise assistant. Follow instructions exactly."}],
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.0}
        )
        return response["output"]["message"]["content"][0]["text"].strip()
    except Exception as e:
        logger.warning(f"call_bedrock_simple failed: {e}")
        return ""


def summarize_and_store_call(phone_hash: str, conversation_history: list,
                             language: str, agent_used: str):
    """Summarize conversation and update phone_profiles for cross-call memory."""
    if not phone_profiles_table or not phone_hash:
        return
    if not conversation_history or len(conversation_history) < 2:
        return

    try:
        # Use Bedrock to generate a one-sentence summary
        recent = conversation_history[-6:]
        summary_prompt = f"""Summarize this phone conversation in ONE sentence in English, capturing: main topic asked, any specific details mentioned (district, crop type, scheme name, family situation).
Conversation: {json.dumps(recent)}
Reply with only the summary sentence, nothing else."""
        summary = call_bedrock_simple(summary_prompt, max_tokens=60)

        if not summary:
            return

        # Store in phone_profiles
        phone_profiles_table.update_item(
            Key={"phone_hash": phone_hash},
            UpdateExpression="""SET last_topic = :t,
                                   last_call_date = :d,
                                   preferred_agent = :a,
                                   call_count = if_not_exists(call_count, :zero) + :one""",
            ExpressionAttributeValues={
                ":t": summary,
                ":d": datetime.utcnow().strftime("%Y-%m-%d"),
                ":a": agent_used,
                ":one": 1,
                ":zero": 0
            }
        )
        logger.info(f"Cross-call summary stored for {phone_hash[:12]}...")
    except Exception as e:
        logger.warning(f"summarize_and_store_call failed: {e}")


# ── Helpers ──────────────────────────────────────────────────
def ask_again(language: str):
    msgs = {
        "hi": "अरे, सुनाई नहीं दिया। एक बार फिर से बोलिए?",
        "mr": "ऐकू आलं नाही. पुन्हा सांगा ना?",
        "ta": "கேட்கவில்லை. மறுபடியும் சொல்லுங்க?",
        "en": "Sorry, I didn't catch that. Could you say it again?",
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
        "headers": {
            "Content-Type": "text/xml",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": str(twiml)
    }
