# VaaniSeva - Lambda: call-handler
# Languages : Hindi (hi) | Marathi (mr) | Tamil (ta) | English (en)
# TTS       : Sarvam AI (primary, all 4 langs) → Amazon Polly fallback
# STT       : Twilio native Gather speech recognition
# LLM       : OpenAI GPT-4o-mini (primary) → Bedrock fallback
# Memory    : Full conversation history per call from DynamoDB
# Latency   : DynamoDB log on background thread · Single combined TTS · 250 token cap

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

# Optional OpenAI — only loaded if API key is set and package is installed
try:
    from openai import OpenAI as _OpenAI
    _openai_available = True
except ImportError:
    _OpenAI = None
    _openai_available = False

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients ──────────────────────────────────────────────
dynamodb  = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock   = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
s3_client = boto3.client("s3", region_name=os.environ["AWS_REGION"])

calls_table     = dynamodb.Table(os.environ["DYNAMODB_CALLS_TABLE"])
knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── OpenAI client (only if key is set AND package is installed) ───────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
openai_client  = _OpenAI(api_key=OPENAI_API_KEY) if (OPENAI_API_KEY and _openai_available) else None
LLM_PROVIDER   = os.environ.get("LLM_PROVIDER", "bedrock")

# ── Config ───────────────────────────────────────────────────
BEDROCK_MODEL_ID           = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_EMBEDDING_MODEL_ID = os.environ["BEDROCK_EMBEDDING_MODEL_ID"]
SARVAM_API_KEY             = os.environ.get("SARVAM_API_KEY", "")
S3_BUCKET                  = os.environ["S3_DOCUMENTS_BUCKET"]
DATA_GOV_API_KEY           = os.environ.get("DATA_GOV_API_KEY", "")
BASE_URL                   = ""  # Set at runtime from API Gateway event

# ── Distress keywords (multi-language) ─────────────────────────
DISTRESS_IMMEDIATE = [
    "मरना चाहता", "जीना नहीं चाहता", "जिंदगी से थक गया",
    "आत्महत्या", "suicide", "want to die", "end my life",
    "koi fayda nahi jeene ka", "जीने का मन नहीं",
    "आपने आप को खत्म", "khatam karna chahta",
]
DISTRESS_ELEVATED = [
    "बहुत थका", "कोई सहारा नहीं", "bahut akela", "koi nahi sunata",
    "can't go on", "no point", "hopeless", "निराश", "depression",
]
DANGER_IMMEDIATE = [
    "मार रहे हैं", "बचाओ", "bachao", "help police", "पुलिस बुलाओ",
    "maar rahe", "खतरा", "danger", "attack", "हिंसा",
]

# ── Intent keywords (for routing to live APIs) ───────────────────
MARKET_PRICE_KEYWORDS = [
    "bhaav", "bhav", "भाव", "भाव", "rate", "price", "mandi", "मंडी",
    "kya chal raha", "kitne ka", "दाम", "today price", "aaj ka",
]
WEATHER_KEYWORDS = [
    "baarish", "बारिश", "weather", "मौसम", "barsat", "बरसात",
    "aandhiyan", "आंधी", "garmi", "ठंड", "rain", "temperature",
]

# ── Language config ──────────────────────────────────────────
LANG_CONFIG = {
    "hi": {
        "sarvam_code": "hi-IN",
        "sarvam_speaker": "anushka",     # only working hi-IN speaker on bulbul:v2
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "hi-IN",
        "digit": "1",
    },
    "mr": {
        "sarvam_code": "mr-IN",
        "sarvam_speaker": "manisha",     # distinct Marathi voice
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "mr-IN",
        "digit": "2",
    },
    "ta": {
        "sarvam_code": "ta-IN",
        "sarvam_speaker": "vidya",       # distinct from Hindi voice
        "polly_voice": "Polly.Aditi",
        "twilio_speech_lang": "ta-IN",
        "digit": "3",
    },
    "en": {
        "sarvam_code": "en-IN",
        "sarvam_speaker": "arya",        # clear English voice
        "polly_voice": "Polly.Raveena",
        "twilio_speech_lang": "en-IN",
        "digit": "4",
    },
}

DIGIT_TO_LANG = {v["digit"]: k for k, v in LANG_CONFIG.items()}

# ── System prompt — warm, human, conversational ─────────────
SYSTEM_PROMPT = """You are VaaniSeva (वाणीसेवा) — think of yourself as a warm, knowledgeable friend who happens to know everything. You're talking to someone on the phone. Be natural. Be human. Have personality.

Who you are:
- A genuinely helpful AI assistant available to EVERYONE via a simple phone call
- You speak like a caring, smart friend — not a robot or government helpline
- You have real warmth — use phrases like "बिल्कुल!" "अच्छा सवाल है!" "चिंता मत करो" naturally
- You remember everything said earlier in this call and build on it

What you can help with (and you're GREAT at all of these):
1. **Government schemes** — PM-Kisan, Ayushman Bharat, MGNREGA, Ujjwala, Mudra loans, Atal Pension, Fasal Bima, SVANidhi, scholarships, housing, and 30+ more. You know eligibility, documents needed, how to apply, helpline numbers.
2. **Farming & agriculture** — crop selection for their soil/season, organic methods, pest control, when to sow/harvest, mandi prices, weather impact, irrigation tips, government subsidies on seeds/fertilizers
3. **Health & wellness** — common illnesses, first aid, when to see a doctor, nearest PHC/CHC info, ASHA worker roles, maternal health, child nutrition, vaccination schedules, mental health awareness
4. **Money & finance** — how to open a bank account, save money, get loans, insurance explained simply, SHG/microfinance, digital payments (UPI), avoiding fraud
5. **Education** — school enrollment, scholarships (national + state), mid-day meals, vocational training, skill development programs, distance learning
6. **Legal rights & documents** — Aadhaar, ration card, voter ID, caste certificate, land records, RTI filing, labour rights, women's rights, domestic violence helplines
7. **Daily life problems** — electricity complaints, water issues, road repair, PDS shop problems, pension delays — guide them on WHO to contact and HOW
8. **General knowledge & curiosity** — answer ANY question they're curious about. If a farmer asks "why is the sky blue?" — answer it! Treat every question with respect.
9. **Emotional support** — if someone sounds stressed, lonely, or upset, be compassionate. Listen. Suggest helplines if needed (iCall: 9152987821, Vandrevala: 1860-2662-345).

How you talk:
- This is a PHONE CALL — keep responses to 3-4 short sentences. Conversational, not essay-style.
- Sound like a real person, not a textbook. Use everyday language.
- Match their energy — if they're excited, be enthusiastic. If worried, be reassuring.
- Use the SAME language they speak. Hindi → pure Devanagari. Marathi → Marathi. Tamil → Tamil. English → simple English. NEVER MIX SCRIPTS.
- DON'T just dump info — have a conversation. Ask follow-up questions naturally: "आपके परिवार में कितने लोग हैं? उसके हिसाब से बताता हूँ" or "Which state are you from? That'll help me give better info."
- If you don't know something, say "मुझे इसकी पूरी जानकारी नहीं है, लेकिन आप इस नंबर पर कॉल कर सकते हैं..." — be honest, but always give a next step.
- NEVER say "I'm just an AI" or "I don't have feelings" — you're VaaniSeva, a helpful friend on the phone.
- Add small human touches: "अच्छा", "हाँ बिल्कुल", "सही बात है" etc.

Remember: You're not a government bot. You're the smartest, kindest friend these people have ever called. Make them feel heard. Make them feel helped. Make them want to call back."""


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
    call_sid    = params.get("CallSid", str(uuid.uuid4()))
    from_number = params.get("From", "unknown")

    # Save call to DynamoDB (background — don't block the greeting)
    def _save_call():
        try:
            calls_table.put_item(Item={
                "call_id": call_sid,
                "timestamp": int(datetime.now().timestamp()),
                "from_number": from_number,
                "status": "in-progress",
                "language": "hi",
                "queries_count": 0,
                "conversation_history": []
            })
        except Exception as e:
            logger.warning(f"DynamoDB save call failed: {e}")
    threading.Thread(target=_save_call, daemon=True).start()

    def s3_url(key):
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": f"static-audio/{key}"},
            ExpiresIn=3600,
        )

    response   = VoiceResponse()
    action_url = f"{BASE_URL}/voice/language" if BASE_URL else "/voice/language"
    gather     = Gather(num_digits=1, action=action_url, method="POST", timeout=10)

    # Play each language clip sequentially — each in its own native voice
    # Files generated by scripts/generate_welcome_audio.py
    for clip in ["welcome_intro.wav", "welcome_hi.wav", "welcome_mr.wav",
                 "welcome_ta.wav", "welcome_en.wav"]:
        try:
            gather.play(s3_url(clip))
        except Exception:
            pass  # skip missing clips silently

    response.append(gather)

    # No-input fallback
    try:
        response.play(s3_url("no_input.wav"))
    except Exception:
        tts_say(response, "कुछ सुनाई नहीं दिया। कृपया दोबारा कॉल करें।", "hi")

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

    # ── Safety check — before any LLM processing ─────────────────
    safety = check_safety(speech_text, language)
    if safety == "danger_immediate":
        return respond_danger(language)
    if safety == "distress_immediate":
        return respond_distress_crisis(language)

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

    # ── Intent routing ────────────────────────────────────
    intent = classify_intent(speech_text)
    logger.info(f"Intent: {intent}")

    try:
        if intent == "mandi_price":
            answer = fetch_mandi_price_response(speech_text, language)
        else:
            answer = rag_pipeline(speech_text, language, call_sid)
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        answer = error_msgs.get(language, error_msgs["en"])

    # Soft distress check — log elevated concern, don’t interrupt call
    if safety == "distress_elevated":
        threading.Thread(
            target=log_distress, args=(call_sid, speech_text, 0.55), daemon=True
        ).start()
        # Gently acknowledge at end of answer
        comfort = {
            "hi": " और भई, अगर कभी मन भारी लगे तो iCall पर कॉल करना: 9152987821",
            "en": " And if things feel heavy, please call iCall: 9152987821",
            "mr": " आणि मन जड वाटल्यास iCall कडे कॉल करा: 9152987821",
            "ta": " மனம் கஷ்டப்பட்டால் iCall அழைக்கவும்: 9152987821",
        }
        answer = answer + comfort.get(language, "")

    follow_up    = follow_ups.get(language, follow_ups["en"])
    goodbye      = goodbyes.get(language, goodbyes["en"])
    cfg          = LANG_CONFIG.get(language, LANG_CONFIG["en"])
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

    threading.Thread(
        target=log_query,
        args=(call_sid, speech_text, answer, language),
        daemon=True
    ).start()

    return twiml_response(response)


# ── Intent Classification ────────────────────────────────────
def classify_intent(text: str) -> str:
    """Fast keyword-based intent router. Returns intent string."""
    t = text.lower()
    if any(k in t for k in MARKET_PRICE_KEYWORDS):
        return "mandi_price"
    if any(k in t for k in WEATHER_KEYWORDS):
        return "weather"
    return "general"


def check_safety(text: str, language: str = "hi") -> str:
    """Returns 'safe', 'distress_elevated', 'distress_immediate', or 'danger_immediate'."""
    t = text.lower()
    if any(k.lower() in t for k in DANGER_IMMEDIATE):
        return "danger_immediate"
    if any(k.lower() in t for k in DISTRESS_IMMEDIATE):
        return "distress_immediate"
    if any(k.lower() in t for k in DISTRESS_ELEVATED):
        return "distress_elevated"
    return "safe"


def respond_danger(language: str):
    """Hardcoded police/emergency response — no LLM latency."""
    msgs = {
        "hi": "अभी तुरंत 100 पर कॉल करें। मैं आपके साथ हूं। सुरक्षित रहिए।",
        "en": "Please call 100 immediately. I'm with you. Stay safe.",
        "mr": "तात्काळ 100 वर कॉल करा. मी तुमच्याबरोबर आहे.",
        "ta": "உடனடியாக 100 அழைக்கவும். நான் உங்களுடன் இருக்கிறேன்.",
    }
    response = VoiceResponse()
    tts_say(response, msgs.get(language, msgs["en"]), language)
    return twiml_response(response)


def respond_distress_crisis(language: str):
    """Hardcoded mental health crisis response with helpline — no LLM."""
    msgs = {
        "hi": "मैं सुन रहा हूँ। आप अकेले नहीं हैं। अभी iCall पर कॉल करिए: 9152987821. वे सुनेंगे।",
        "en": "I hear you. You are not alone. Please call iCall right now: 9152987821. They will listen.",
        "mr": "मी ऐकतोय. तुम्ही एकटे नाही. iCall ला कॉल करा: 9152987821.",
        "ta": "நான் கேட்கிறேன். நீங்கள் தனியில்லை. iCall அழைக்கவும்: 9152987821.",
    }
    response = VoiceResponse()
    tts_say(response, msgs.get(language, msgs["en"]), language)
    return twiml_response(response)


def log_distress(call_sid: str, text: str, score: float):
    """Log elevated distress signal to DynamoDB for pattern tracking."""
    try:
        ts = get_call_timestamp(call_sid)
        calls_table.update_item(
            Key={"call_id": call_sid, "timestamp": ts},
            UpdateExpression="SET distress_score = :s, distress_text = :t",
            ExpressionAttributeValues={":s": str(score), ":t": text[:200]}
        )
    except Exception as e:
        logger.warning(f"Failed to log distress: {e}")


# ── Agmarknet Live Mandi Prices ──────────────────────────────
COMMODITY_MAP = {
    "gehu": "Wheat", "gehun": "Wheat", "गेहूं": "Wheat",
    "chawal": "Rice", "dhaan": "Rice", "धान": "Rice", "चावल": "Rice",
    "pyaz": "Onion", "pyaaz": "Onion", "प्याज": "Onion",
    "aloo": "Potato", "aaloo": "Potato", "आलू": "Potato",
    "tamatar": "Tomato", "टमाटर": "Tomato",
    "lahsun": "Garlic", "लहसुन": "Garlic",
    "sarson": "Mustard", "सरसों": "Mustard",
    "makka": "Maize", "corn": "Maize",
    "soyabean": "Soyabean", "soya": "Soyabean",
    "cotton": "Cotton", "kapas": "Cotton", "कपास": "Cotton",
    "ganna": "Sugarcane", "sugarcane": "Sugarcane", "गन्ना": "Sugarcane",
}

STATE_MAP = {
    "up": "Uttar Pradesh", "uttar pradesh": "Uttar Pradesh",
    "mp": "Madhya Pradesh", "madhya pradesh": "Madhya Pradesh",
    "maha": "Maharashtra", "maharashtra": "Maharashtra",
    "raj": "Rajasthan", "rajasthan": "Rajasthan",
    "punjab": "Punjab", "haryana": "Haryana",
    "bihar": "Bihar", "gujarat": "Gujarat",
    "karnataka": "Karnataka", "ap": "Andhra Pradesh",
    "telangana": "Telangana", "tn": "Tamil Nadu", "tamilnadu": "Tamil Nadu",
}


def fetch_mandi_price_response(query: str, language: str) -> str:
    """Detect commodity + state from voice query, fetch Agmarknet, return spoken response."""
    q = query.lower()

    commodity_en = next((eng for kw, eng in COMMODITY_MAP.items() if kw in q), None)
    state_en     = next((eng for kw, eng in STATE_MAP.items() if kw in q), None)

    if not commodity_en:
        # Can't identify commodity — fall back to RAG+LLM
        return rag_pipeline(query, language)

    try:
        records = _call_agmarknet(commodity_en, state_en)
    except Exception as e:
        logger.warning(f"Agmarknet API error: {e}")
        return rag_pipeline(query, language)

    if not records:
        no_data = {
            "hi": f"आज {commodity_en} का भाव अभी उपलब्ध नहीं है। कल सुबह फिर पूछें।",
            "mr": f"आज {commodity_en} चा भाव उपलब्ध नाही. उद्या सकाळी विचारा.",
            "ta": f"இன்று {commodity_en} விலை கிடைக்கவில்லை. நாளை காலை கேளுங்கள்.",
            "en": f"Today's {commodity_en} price is not available. Try tomorrow morning.",
        }
        return no_data.get(language, no_data["en"])

    rec    = records[0]
    modal  = rec.get("modal_price", "N/A")
    min_p  = rec.get("min_price", "N/A")
    max_p  = rec.get("max_price", "N/A")
    market = rec.get("market", "")
    state_name = rec.get("state", state_en or "")

    if language == "hi":
        return (f"आज {state_name} के {market} मंडी में {commodity_en} का भाव "
                f"₹{modal} प्रति क्विंटल चल रहा है। "
                f"अधिकतम ₹{max_p}, न्यूनतम ₹{min_p}।")
    if language == "mr":
        return (f"आज {state_name} मधील {market} गंजीत {commodity_en} चा भाव "
                f"₹{modal} प्रति क्विंटल आहे. कमाल ₹{max_p}, किमान ₹{min_p}.")
    if language == "ta":
        return (f"இன்று {state_name}ல் {market} சந்தையில் {commodity_en} விலை "
                f"₹{modal} குவிண்டல். அதிகபட்சம் ₹{max_p}, குறைந்தபட்சம் ₹{min_p}.")
    return (f"Today in {market}, {state_name}: {commodity_en} is at ₹{modal}/quintal. "
            f"Max: ₹{max_p}, Min: ₹{min_p}.")


def _call_agmarknet(commodity: str, state: str = None) -> list:
    """Call data.gov.in Agmarknet API. Returns list of price records."""
    if not DATA_GOV_API_KEY:
        logger.info("No DATA_GOV_API_KEY set — skipping Agmarknet")
        return []
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "filters[commodity]": commodity,
        "limit": 3,
    }
    if state:
        params["filters[state]"] = state
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    return r.json().get("records", [])


# ── RAG Pipeline (with conversation memory) ──────────────────
def rag_pipeline(query: str, language: str, call_sid: str = "") -> str:
    embedding = get_embedding(query)
    context   = retrieve_context(embedding, language)
    history   = get_conversation_history(call_sid) if call_sid else []
    return ask_llm(query, context, language, history)


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


def ask_llm(query: str, context: str, language: str, history: list = None) -> str:
    lang_instructions = {
        "hi": "जवाब पूरी तरह हिंदी देवनागरी लिपि में दो। कोई भी अंग्रेजी या रोमन अक्षर मत लिखो।",
        "mr": "उत्तर संपूर्णपणे मराठी लिपीत द्या. कोणतेही इंग्रजी किंवा रोमन अक्षर वापरू नका.",
        "ta": "பதிலை முழுவதுமாக தமிழ் எழுத்தில் கொடுங்கள். எந்த ஆங்கிலமும் ரோமன் எழுத்தும் வேண்டாம்.",
        "en": "Respond in simple, clear English.",
    }
    lang_instruction = lang_instructions.get(language, lang_instructions["en"])

    user_msg = f"""{lang_instruction}

Relevant context from our knowledge base (use if helpful, ignore if not relevant):
{context}

User just said: {query}

Respond naturally in 3-4 short sentences. This is a phone call — be conversational, not robotic."""

    # Try OpenAI first (much better conversational ability)
    if LLM_PROVIDER == "openai" and openai_client:
        try:
            return _ask_openai(user_msg, history or [])
        except Exception as e:
            logger.warning(f"OpenAI failed, falling back to Bedrock: {e}")

    # Bedrock fallback
    return _ask_bedrock(user_msg)


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


def _ask_bedrock(user_msg: str) -> str:
    """Fallback: Bedrock Converse API — model-agnostic, works with Llama 3.3 70B."""
    response = bedrock.converse(
        modelId=BEDROCK_MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user_msg}]}],
        inferenceConfig={"maxTokens": 250, "temperature": 0.5}
    )
    return response["output"]["message"]["content"][0]["text"].strip()


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
