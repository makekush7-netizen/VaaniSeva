# VaaniSeva – Amazon Connect Lambda handler
# Invoked by Contact Flow at specific points during a call.
# Returns flat string-keyed dicts that Contact Flow uses in prompts / attributes.
#
# Shared core: RAG pipeline, Sarvam TTS, DynamoDB — all from handler.py

import json
import os
import uuid
import logging
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ── AWS clients (same as handler.py but imported fresh to avoid circular deps) ─
dynamodb  = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock   = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
s3_client = boto3.client("s3", region_name=os.environ["AWS_REGION"])

calls_table     = dynamodb.Table(os.environ["DYNAMODB_CALLS_TABLE"])
knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

S3_BUCKET = os.environ["S3_DOCUMENTS_BUCKET"]

# Import only the *pure* functions we need from the Twilio handler
# (these don't depend on Twilio objects)
from handler import (
    rag_pipeline,
    sarvam_tts,
    get_call_timestamp,
    SYSTEM_PROMPT,
)


# ══════════════════════════════════════════════════════════════
#  Entry point – called by lambda_handler when event is Connect
# ══════════════════════════════════════════════════════════════

def handle_connect_event(event):
    """
    Amazon Connect sends:
      { "Details": { "ContactData": {...}, "Parameters": {...} }, "Name": "..." }
    Lambda must return a flat dict of string→string pairs.
    """
    details      = event.get("Details", {})
    contact_data = details.get("ContactData", {})
    parameters   = details.get("Parameters", {})
    attributes   = contact_data.get("Attributes", {})

    contact_id      = contact_data.get("ContactId", str(uuid.uuid4()))
    customer_number = (
        contact_data.get("CustomerEndpoint", {}).get("Address", "unknown")
    )

    action = parameters.get("action", "init")
    logger.info(f"Connect action={action} contact={contact_id} from={customer_number}")

    if action == "init":
        return _init_call(contact_id, customer_number)
    elif action == "set_language":
        return _set_language(contact_id, parameters, attributes)
    elif action == "query":
        return _handle_query(contact_id, parameters, attributes)
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


# ── init: first Lambda invocation when call starts ───────────
def _init_call(contact_id, customer_number):
    calls_table.put_item(Item={
        "call_id":              contact_id,
        "timestamp":            int(datetime.now().timestamp()),
        "from_number":          customer_number,
        "status":               "in-progress",
        "language":             "en",
        "queries_count":        0,
        "conversation_history": [],
        "source":               "amazon-connect",
    })
    return {
        "status":        "ok",
        "welcome_hi":    "वाणीसेवा में आपका स्वागत है। हिंदी के लिए एक दबाएं।",
        "welcome_en":    "Welcome to VaaniSeva. For English, press 2.",
        "welcome_full":  "वाणीसेवा में आपका स्वागत है। हिंदी के लिए एक दबाएं। Welcome to VaaniSeva. For English, press 2.",
    }


# ── set_language: after user presses 1 or 2 ──────────────────
def _set_language(contact_id, parameters, attributes):
    digit    = parameters.get("digit", "2")
    language = "hi" if digit == "1" else "en"

    try:
        ts = get_call_timestamp(contact_id)
        calls_table.update_item(
            Key={"call_id": contact_id, "timestamp": ts},
            UpdateExpression="SET #lang = :lang",
            ExpressionAttributeNames={"#lang": "language"},
            ExpressionAttributeValues={":lang": language},
        )
    except Exception as e:
        logger.warning(f"Failed to update language: {e}")

    if language == "hi":
        prompt = "आप कौनसी सरकारी योजना के बारे में जानना चाहते हैं? बोलिए।"
    else:
        prompt = "Which government scheme would you like to know about? Please speak."

    return {
        "status":   "ok",
        "language":  language,
        "prompt":    prompt,
        "polly_voice": "Kajal" if language == "hi" else "Ruth",
        "polly_engine": "neural",
    }


# ── query: after Lex captures user's speech ──────────────────
def _handle_query(contact_id, parameters, attributes):
    speech_text = parameters.get("speech_text", "")
    language    = attributes.get("language", parameters.get("language", "en"))

    logger.info(f"Connect query: '{speech_text}' lang={language}")

    if not speech_text:
        no_input = (
            "कुछ सुनाई नहीं दिया। कृपया दोबारा बोलिए।"
            if language == "hi"
            else "I didn't catch that. Could you please repeat?"
        )
        return {
            "status":       "no_input",
            "answer":       no_input,
            "polly_voice":  "Kajal" if language == "hi" else "Ruth",
            "polly_engine": "neural",
        }

    # ── RAG pipeline (same as Twilio path) ───────────────────
    try:
        answer = rag_pipeline(speech_text, language)
    except Exception as e:
        logger.error(f"Connect RAG error: {e}")
        answer = (
            "मुझे अभी कुछ तकलीफ हो रही है। थोड़ी देर बाद कोशिश करें।"
            if language == "hi"
            else "I'm having trouble right now. Please try again shortly."
        )

    follow_up = (
        "क्या आप और कुछ जानना चाहते हैं?"
        if language == "hi"
        else "Would you like to know anything else?"
    )

    # ── Try Sarvam TTS for higher quality audio ──────────────
    audio_url = sarvam_tts(f"{answer} {follow_up}", language)

    # Log the query
    _log_query(contact_id, speech_text, answer, language)

    return {
        "status":       "ok",
        "answer":       f"{answer} {follow_up}",
        "audio_url":    audio_url or "",       # empty = Contact Flow falls back to Polly
        "polly_voice":  "Kajal" if language == "hi" else "Ruth",
        "polly_engine": "neural",
        "language":     language,
    }


# ── helper ───────────────────────────────────────────────────
def _log_query(contact_id, query, answer, language):
    try:
        ts = get_call_timestamp(contact_id)
        calls_table.update_item(
            Key={"call_id": contact_id, "timestamp": ts},
            UpdateExpression=(
                "SET queries_count = queries_count + :one, "
                "conversation_history = list_append(conversation_history, :entry)"
            ),
            ExpressionAttributeValues={
                ":one":  1,
                ":entry": [{
                    "query":    query,
                    "answer":   answer,
                    "language": language,
                    "ts":       int(datetime.now().timestamp()),
                }],
            },
        )
    except Exception as e:
        logger.warning(f"Connect log_query failed: {e}")
