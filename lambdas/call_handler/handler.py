# VaaniSeva - Lambda: call-handler
# Handles all incoming Twilio voice calls
# Flow: Incoming call → language select → STT → RAG → LLM → TTS → respond

import json
import os
import boto3
import requests
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients ──────────────────────────────────────────────
dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock  = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
polly    = boto3.client("polly", region_name=os.environ["AWS_REGION"])

calls_table     = dynamodb.Table(os.environ["DYNAMODB_CALLS_TABLE"])
knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── Config ───────────────────────────────────────────────────
BEDROCK_MODEL_ID          = os.environ["BEDROCK_MODEL_ID"]
BEDROCK_EMBEDDING_MODEL_ID = os.environ["BEDROCK_EMBEDDING_MODEL_ID"]
BHASHINI_USER_ID          = os.environ.get("BHASHINI_USER_ID", "")
BHASHINI_API_KEY          = os.environ.get("BHASHINI_API_KEY", "")

SYSTEM_PROMPT = """You are VaaniSeva, an AI assistant helping rural Indians access government scheme information via phone.

RULES:
- Respond in the user's language (Hindi or English)
- Use simple, everyday words — no jargon
- Keep answers to 2-3 short sentences max (this is a phone call)
- Only answer about these 5 schemes: PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas Yojana, Sukanya Samriddhi Yojana
- If asked something else, politely say you only know about government schemes
- Never say the word "Claude"
- End every answer by asking if they want to know more"""

# ── Main Lambda handler ──────────────────────────────────────
def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")

    # API Gateway wraps the body as a string
    body = event.get("body", "")
    if isinstance(body, str):
        from urllib.parse import parse_qs
        params = {k: v[0] for k, v in parse_qs(body).items()}
    else:
        params = body or {}

    path = event.get("path", "/voice/incoming")

    if "/incoming" in path:
        return handle_incoming(params)
    elif "/gather" in path:
        return handle_gather(params)
    elif "/language" in path:
        return handle_language_select(params)
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
    gather = Gather(num_digits=1, action="/voice/language", method="POST", timeout=10)
    gather.say(
        "Welcome to VaaniSeva. For Hindi, press 1. For English, press 2. "
        "VaaniSeva mein aapka swagat hai. Hindi ke liye 1 dabayein. English ke liye 2 dabayein.",
        voice="Polly.Raveena"
    )
    response.append(gather)
    response.say("We did not receive your input. Please call again.", voice="Polly.Raveena")

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

    response = VoiceResponse()
    if language == "hi":
        prompt_text = "Aap kaunsi sarkari yojana ke baare mein jaanna chahte hain? Boliye."
        voice = "Polly.Aditi"
    else:
        prompt_text = "Which government scheme would you like to know about? Please speak after the beep."
        voice = "Polly.Raveena"

    gather = Gather(
        input="speech",
        action=f"/voice/gather?lang={language}",
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=10
    )
    gather.say(prompt_text, voice=voice)
    response.append(gather)
    response.say("I did not hear anything. Please call again.", voice=voice)

    return twiml_response(response)


# ── Step 3: User spoke — process query ──────────────────────
def handle_gather(params):
    call_sid    = params.get("CallSid", "")
    speech_text = params.get("SpeechResult", "")
    language    = params.get("lang", "en")

    logger.info(f"Speech: '{speech_text}' | Lang: {language} | Call: {call_sid}")

    if not speech_text:
        return ask_again(language)

    # RAG → LLM pipeline
    try:
        answer = rag_pipeline(speech_text, language, call_sid)
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        answer = (
            "Mujhe abhi kuch takleef ho rahi hai. Thodi der baad try karein."
            if language == "hi"
            else "I'm having trouble right now. Please try again in a moment."
        )

    voice = "Polly.Aditi" if language == "hi" else "Polly.Raveena"
    response = VoiceResponse()

    # Speak the answer
    gather = Gather(
        input="speech",
        action=f"/voice/gather?lang={language}",
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=15
    )
    gather.say(answer, voice=voice)
    response.append(gather)

    # If no follow-up, say goodbye
    goodbye = "Dhanyavaad. VaaniSeva call karne ke liye shukriya." if language == "hi" \
              else "Thank you for calling VaaniSeva. Goodbye."
    response.say(goodbye, voice=voice)

    # Log query to DynamoDB
    log_query(call_sid, speech_text, answer, language)

    return twiml_response(response)


# ── RAG Pipeline ─────────────────────────────────────────────
def rag_pipeline(query: str, language: str, call_sid: str) -> str:
    # 1. Generate embedding for the query
    embedding = get_embedding(query)

    # 2. Find relevant scheme info from DynamoDB
    context = retrieve_context(embedding, language)

    # 3. Ask Claude via Bedrock
    answer = ask_claude(query, context, language)

    return answer


def get_embedding(text: str) -> list:
    response = bedrock.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def retrieve_context(query_embedding: list, language: str) -> str:
    """Simple cosine similarity search against vaaniseva-vectors table."""
    import math

    def cosine_similarity(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        return dot / (mag_a * mag_b + 1e-9)

    # Scan vectors table (small dataset for hackathon — acceptable)
    items = vectors_table.scan().get("Items", [])
    if not items:
        return "No scheme information loaded yet."

    scored = []
    for item in items:
        stored_embedding = item.get("embedding", [])
        if stored_embedding:
            score = cosine_similarity(query_embedding, stored_embedding)
            scored.append((score, item))

    # Top 3 matches
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
    lang_key = "hi" if language == "hi" else "en"
    context_parts = [item.get(f"text_{lang_key}", item.get("text", "")) for _, item in top]
    return "\n\n".join(context_parts)


def ask_claude(query: str, context: str, language: str) -> str:
    lang_instruction = "Respond in Hindi." if language == "hi" else "Respond in English."

    messages = [
        {
            "role": "user",
            "content": f"""{lang_instruction}

Context from government scheme database:
{context}

User's question: {query}

Answer in 2-3 short sentences suitable for a phone call."""
        }
    ]

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0.3,
            "system": SYSTEM_PROMPT,
            "messages": messages
        }),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"].strip()


# ── Helpers ──────────────────────────────────────────────────
def ask_again(language: str):
    voice = "Polly.Aditi" if language == "hi" else "Polly.Raveena"
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"/voice/gather?lang={language}",
        method="POST",
        language="hi-IN" if language == "hi" else "en-IN",
        speech_timeout="auto",
        timeout=10
    )
    msg = "Kripya dobara boliye." if language == "hi" else "Sorry, I didn't catch that. Please say it again."
    gather.say(msg, voice=voice)
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
