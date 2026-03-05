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
        "sarvam_speaker": "manisha",
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

# ── System prompt — warm, human, conversational ─────────────
SYSTEM_PROMPT = """तुम वाणीसेवा (VaaniSeva) हो — एक गर्मजोशी से भरी, समझदार दीदी जो हर सवाल का जवाब जानती है। तुम फोन पर भी बात करती हो और वेब चैट पर भी। तुम्हारी आवाज़ एक औरत की है — हमेशा "मैं बताती हूँ", "मैं ढूँढती हूँ", "मुझे पता है" बोलो। कभी भी "बताता हूँ" या पुरुष भाषा मत बोलो।

तुम कौन हो:
- VaaniSeva (वाणीसेवा) — "AI for Bharat Hackathon 2026" के लिए बनाई गई एक voice-first AI assistant
- तुम गाँव और शहर दोनों के लोगों की मदद करती हो — सरकारी योजनाएँ, खेती, स्वास्थ्य, पैसा, पढ़ाई, कानूनी हक़, रोज़मर्रा की दिक्कतें, और कोई भी सवाल
- तुम एक simple phone call या website पर उपलब्ध हो — कोई app download करने की ज़रूरत नहीं
- तुम 4 भाषाओं में बात करती हो: हिंदी, मराठी, तमिल, और English
- तुम्हारा लहज़ा एक caring बड़ी बहन/दीदी का है — ना रोबोट, ना सरकारी हेल्पलाइन

तुम किस-किस चीज़ में मदद कर सकती हो:
1. सरकारी योजनाएँ — PM-Kisan, Ayushman Bharat, MGNREGA, उज्ज्वला, मुद्रा लोन, अटल पेंशन, फसल बीमा, SVANidhi, छात्रवृत्ति, आवास, और 30+ योजनाएँ। पात्रता, ज़रूरी दस्तावेज़, आवेदन कैसे करें, हेल्पलाइन नंबर — सब बताती हूँ।
2. खेती — फसल चुनाव, जैविक तरीके, कीट नियंत्रण, बुवाई/कटाई, मंडी भाव, मौसम, सिंचाई, बीज-खाद सब्सिडी
3. स्वास्थ्य — आम बीमारियाँ, प्राथमिक उपचार, PHC/CHC जानकारी, टीकाकरण, माँ-बच्चे की सेहत, मानसिक स्वास्थ्य
4. पैसा और बैंकिंग — खाता खोलना, बचत, लोन, बीमा, SHG, UPI, फ्रॉड से बचाव
5. शिक्षा — स्कूल दाखिला, छात्रवृत्ति, मिड-डे मील, स्किल ट्रेनिंग, दूरस्थ शिक्षा
6. कानूनी हक़ — आधार, राशन कार्ड, वोटर ID, जाति प्रमाणपत्र, भूमि रिकॉर्ड, RTI, श्रमिक अधिकार, महिला अधिकार
7. रोज़मर्रा — बिजली शिकायत, पानी, सड़क, PDS दुकान, पेंशन — किससे और कैसे बात करें
8. कोई भी सवाल — "आसमान नीला क्यों है?" हो या "चाँद पर कौन गया" — बताती हूँ! हर सवाल का सम्मान करो।
9. भावनात्मक सहारा — अगर कोई परेशान लगे, तो प्यार से सुनो। ज़रूरत हो तो helpline: iCall 9152987821, Vandrevala 1860-2662-345

कैसे बात करनी है:
- जवाब 3-4 छोटे वाक्यों में दो। बातचीत जैसा, लेख जैसा नहीं।
- असली इंसान जैसी बात करो — "अच्छा!", "हाँ बिल्कुल!", "चिंता मत करो", "सही बात है" जैसे शब्द naturally बोलो।
- Follow-up सवाल पूछो: "आपके परिवार में कितने लोग हैं? उसके हिसाब से बताती हूँ" या "कौन से राज्य से हो? बेहतर जानकारी दे पाऊँगी।"
- अगर कोई चीज़ नहीं पता तो ईमानदारी से बोलो: "इसकी पूरी जानकारी मेरे पास नहीं है, लेकिन आप इस नंबर पर बात कर सकते हैं..." — हमेशा अगला कदम बताओ।
- कभी मत बोलो "I'm just an AI" या "मैं सिर्फ AI हूँ" — तुम वाणीसेवा हो, एक भरोसेमंद दीदी।

=== STRICT LANGUAGE RULE ===
This is the MOST IMPORTANT rule. You MUST follow the language specified in the user message.
- If told "Hindi" or "hi" → reply ONLY in Devanagari Hindi. NO English words, NO Roman script.
- If told "Marathi" or "mr" → reply ONLY in Marathi script. NO Hindi mixing.
- If told "Tamil" or "ta" → reply ONLY in Tamil script. NO English, NO Hindi.
- If told "English" or "en" → reply ONLY in simple English.
- NEVER mix scripts. NEVER write Hindi in Roman letters. NEVER put English words in a Hindi response.
- Proper nouns (PM-Kisan, Ayushman Bharat, MGNREGA) can stay in English.
========================

याद रखो: तुम सरकारी बॉट नहीं हो। तुम इन लोगों की सबसे समझदार, सबसे प्यारी दीदी हो।"""


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

    # ── Twilio voice endpoints ───────────────────────────────
    body = event.get("body", "")
    if isinstance(body, str):
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body).items()}
    else:
        params = body or {}

    if "/incoming" in path:
        return handle_incoming(params)
    elif "/language" in path:
        return handle_language_select(params)
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
            "Access-Control-Allow-Methods": "GET,POST,PUT,OPTIONS",
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
        prod_url = os.environ.get("API_BASE_URL", "https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod")
        call = twilio_client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=f"{prod_url}/voice/incoming",
            method="POST",
        )

        # Log callback
        calls_table.put_item(Item={
            "call_id": f"cb-{uuid.uuid4()}",
            "timestamp": int(datetime.now().timestamp()),
            "from_number": phone_number,
            "status": "web-callback",
            "language": "hi",
            "queries_count": 0,
            "conversation_history": [],
        })

        return cors_json_response(200, {
            "status": "calling",
            "message": "Call initiated! Pick up in ~10 seconds.",
            "call_sid": call.sid,
        })
    except Exception as e:
        logger.error(f"Call initiate failed: {e}")
        err = str(e).lower()
        if "unverified" in err:
            return cors_json_response(400, {"error": "Number not verified on trial account. Call us at +1 260 204 8966."})
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


def handle_chat(event):
    """POST /chat — Text-based chat for web fallback."""
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_json_response(400, {"error": "Invalid JSON body"})

    query = body.get("query", "").strip()
    language = body.get("language", "hi")
    session_id = body.get("session_id", "")

    if not query:
        return cors_json_response(400, {"error": "Empty query"})

    # Optional: inject user profile context if authenticated
    user_profile = _get_user_from_event(event)
    profile_context = _build_profile_context(user_profile) if user_profile else ""

    try:
        answer = rag_pipeline(query, language, session_id, profile_context=profile_context)
    except Exception as e:
        logger.error(f"Chat RAG error: {e}")
        answer = "I'm having trouble right now. Please try again."

    # Generate TTS audio
    audio_url = sarvam_tts(answer, language)

    return cors_json_response(200, {
        "answer": answer,
        "audio_url": audio_url or "",
        "language": language,
    })


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


# ── Step 1: New call comes in ────────────────────────────────
def handle_incoming(params):
    call_sid    = params.get("CallSid", str(uuid.uuid4()))
    from_number = params.get("From", "unknown")
    lang_param  = params.get("lang", "").strip()  # Browser calls pre-select language

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
        "queries_count": 0,
        "conversation_history": [],
        "user_id": caller_profile.get("user_id", "") if caller_profile else "",
        "source": "browser" if lang_param else "phone",
    })

    # Browser call: skip language menu, greet in chosen language and go to gather
    if lang_param and lang_param in LANG_CONFIG:
        return _browser_call_welcome(call_sid, language)

    response = VoiceResponse()
    action_url = f"{BASE_URL}/voice/language" if BASE_URL else "/voice/language"
    gather = Gather(num_digits=1, action=action_url, method="POST", timeout=10)

    # Play pre-recorded welcome clips sequentially: intro → Hindi → Marathi → Tamil → English
    for key in ["welcome_intro", "welcome_hi", "welcome_mr", "welcome_ta", "welcome_en"]:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": f"static-audio/{key}.wav"},
            ExpiresIn=3600,
        )
        gather.play(url)
    response.append(gather)

    # Pre-recorded Sarvam TTS no-input fallback from S3
    no_input_url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": "static-audio/no_input.wav"},
        ExpiresIn=3600,
    )
    response.play(no_input_url)

    return twiml_response(response)


def _browser_call_welcome(call_sid: str, language: str):
    """Skip DTMF menu for browser calls — greet in chosen language and open gather."""
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
    gather_url = f"{BASE_URL}/voice/gather?lang={language}" if BASE_URL else f"/voice/gather?lang={language}"

    response = VoiceResponse()
    gather   = Gather(
        input="speech",
        action=gather_url,
        method="POST",
        language=cfg["twilio_speech_lang"],
        speech_timeout="auto",
        timeout=15,
    )
    tts_say(gather, greetings.get(language, greetings["en"]), language)
    response.append(gather)
    tts_say(response, fallbacks.get(language, fallbacks["en"]), language)
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
        "hi": "हाँ जी, बताइए आपका सवाल! मैं सुन रही हूँ।",
        "mr": "हो, बोला तुमचा प्रश्न! मी ऐकतेय.",
        "ta": "சொல்லுங்க, நான் கேட்கிறேன்!",
        "en": "Go ahead, I'm listening! What would you like to know?",
    }
    fallbacks = {
        "hi": "कुछ सुनाई नहीं दिया। दोबारा कॉल करके बात कीजिए ना।",
        "mr": "काही ऐकू आलं नाही. पुन्हा कॉल करा ना.",
        "ta": "எதுவும் கேட்கவில்லை. மீண்டும் அழைக்கவும்.",
        "en": "I couldn't hear you. Please try calling again.",
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

    try:
        # Inject profile context if caller is a registered user
        profile_context = ""
        try:
            ts = get_call_timestamp(call_sid)
            call_item = calls_table.get_item(Key={"call_id": call_sid, "timestamp": ts}).get("Item", {})
            user_id = call_item.get("user_id", "")
            if user_id:
                user_result = users_table.get_item(Key={"user_id": user_id})
                caller = user_result.get("Item")
                if caller:
                    profile_context = _build_profile_context(caller)
        except Exception as pe:
            logger.warning(f"Profile lookup for call {call_sid}: {pe}")

        answer = rag_pipeline(speech_text, language, call_sid, profile_context=profile_context)
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
    """Fetch relevant scheme data from data.gov.in API. Returns summary text or empty string."""
    if not DATA_GOV_API_KEY:
        return ""
    try:
        # Search government schemes/resources relevant to the query
        # data.gov.in API: https://data.gov.in/backend/dmspublic/v1/resource
        params = {
            "api-key": DATA_GOV_API_KEY,
            "format": "json",
            "filters[search]": query[:100],
            "limit": 3,
        }
        resp = requests.get(
            "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
            params=params,
            timeout=5,
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        records = data.get("records", [])
        if not records:
            return ""
        summaries = []
        for rec in records[:3]:
            title = rec.get("scheme_name") or rec.get("title") or ""
            desc = rec.get("description") or rec.get("scheme_description") or ""
            ministry = rec.get("ministry") or rec.get("department") or ""
            if title:
                entry = f"• {title}"
                if ministry:
                    entry += f" (Ministry: {ministry})"
                if desc:
                    entry += f": {desc[:200]}"
                summaries.append(entry)
        return "\n".join(summaries)
    except Exception as e:
        logger.warning(f"data.gov.in fetch failed: {e}")
        return ""


def rag_pipeline(query: str, language: str, call_sid: str = "", profile_context: str = "") -> str:
    embedding = get_embedding(query)
    context   = retrieve_context(embedding, language)

    # Augment context with live data.gov.in data if API key is set
    live_data = _fetch_data_gov(query) if DATA_GOV_API_KEY else ""
    if live_data:
        context = f"{context}\n\n--- Live Government Data (data.gov.in) ---\n{live_data}"

    history   = get_conversation_history(call_sid) if call_sid else []
    return ask_llm(query, context, language, history, profile_context=profile_context)


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


def ask_llm(query: str, context: str, language: str, history: list = None, profile_context: str = "") -> str:
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

    # Try OpenAI first if configured
    if LLM_PROVIDER == "openai" and openai_client:
        try:
            return _ask_openai(user_msg, history or [])
        except Exception as e:
            logger.warning(f"OpenAI failed, falling back to Bedrock: {e}")

    # Bedrock (primary)
    return _ask_bedrock(user_msg, history or [])


def _ask_openai(user_msg: str, history: list) -> str:
    """Call OpenAI GPT-4o-mini with full conversation history."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 10 turns max to stay within context)
    for turn in (history or [])[-10:]:
        messages.append({"role": "user", "content": turn.get("query", "")})
        messages.append({"role": "assistant", "content": turn.get("answer", "")})

    # Current user message
    messages.append({"role": "user", "content": user_msg})

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=250,
        temperature=0.7,  # more creative/human
    )
    return response.choices[0].message.content.strip()


def _ask_bedrock(user_msg: str, history: list = None) -> str:
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
        system=[{"text": SYSTEM_PROMPT}],
        messages=messages,
        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.7,
        }
    )
    return response["output"]["message"]["content"][0]["text"].strip()


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
