# VaaniSeva — Call Initiator Lambda
# POST /call/initiate  { "phone_number": "+91XXXXXXXXXX" }
# 1. Validate E.164 format
# 2. DynamoDB rate-limit: max 2 calls/hour per number
# 3. Twilio outbound call → routes into VaaniSeva phone pipeline
# 4. Returns { "status": "calling" } with CORS headers

import json
import os
import re
import time
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
RATE_LIMIT_TABLE = os.environ.get("DYNAMODB_CALLS_TABLE", "vaaniseva-calls")
rate_table = dynamodb.Table(RATE_LIMIT_TABLE)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "+12602048966")
API_BASE_URL = os.environ.get("API_BASE_URL", "https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod")

# Rate limit: max calls per hour per number
MAX_CALLS_PER_HOUR = 2


def cors_response(status_code, body):
    """Return JSON response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def validate_e164(phone_number):
    """Validate E.164 phone number format."""
    pattern = r"^\+[1-9]\d{6,14}$"
    return bool(re.match(pattern, phone_number))


def check_rate_limit(phone_number):
    """Check if phone number has exceeded rate limit (2 calls/hour)."""
    one_hour_ago = int(time.time()) - 3600
    try:
        # Query call records for this number in the last hour
        # We use a scan with filter since from_number is not a key
        response = rate_table.scan(
            FilterExpression="from_number = :phone AND #ts > :cutoff AND #src = :src",
            ExpressionAttributeNames={"#ts": "timestamp", "#src": "status"},
            ExpressionAttributeValues={
                ":phone": phone_number,
                ":cutoff": one_hour_ago,
                ":src": "web-callback",
            },
            Select="COUNT",
        )
        count = response.get("Count", 0)
        return count >= MAX_CALLS_PER_HOUR
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        return False  # Allow call if rate limit check fails


def log_callback_request(phone_number):
    """Log the callback request to DynamoDB."""
    import uuid
    try:
        rate_table.put_item(Item={
            "call_id": f"cb-{uuid.uuid4()}",
            "timestamp": int(time.time()),
            "from_number": phone_number,
            "status": "web-callback",
            "language": "hi",
            "queries_count": 0,
            "conversation_history": [],
        })
    except Exception as e:
        logger.warning(f"Failed to log callback request: {e}")


def lambda_handler(event, context):
    logger.info(f"Call initiator event: {json.dumps(event)}")

    # Handle CORS preflight
    http_method = event.get("httpMethod", "POST")
    if http_method == "OPTIONS":
        return cors_response(200, {"status": "ok"})

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return cors_response(400, {"error": "Invalid JSON body"})

    phone_number = body.get("phone_number", "").strip()

    # Auto-prepend +91 if needed
    if phone_number and not phone_number.startswith("+"):
        phone_number = f"+91{phone_number}"

    # Validate phone number
    if not phone_number or not validate_e164(phone_number):
        return cors_response(400, {
            "error": "Invalid phone number. Please enter a valid number with country code (e.g., +91XXXXXXXXXX)."
        })

    # Rate limit check
    if check_rate_limit(phone_number):
        return cors_response(429, {
            "error": "You've reached the maximum of 2 calls per hour. Please try again later."
        })

    # Initiate Twilio call
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        call = client.calls.create(
            to=phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{API_BASE_URL}/voice/incoming",
            method="POST",
        )

        logger.info(f"Call initiated: {call.sid} to {phone_number}")

        # Log the callback request
        log_callback_request(phone_number)

        return cors_response(200, {
            "status": "calling",
            "message": "Call initiated! Pick up your phone in ~10 seconds.",
            "call_sid": call.sid,
        })

    except Exception as e:
        logger.error(f"Twilio call failed: {e}")
        error_msg = str(e)

        # Friendly error messages
        if "unverified" in error_msg.lower():
            return cors_response(400, {
                "error": "This number is not verified on our trial account. Please call us directly at +1 978 830 9619."
            })
        elif "invalid" in error_msg.lower() or "not a valid" in error_msg.lower():
            return cors_response(400, {
                "error": "Invalid phone number format. Please check and try again."
            })
        else:
            return cors_response(500, {
                "error": "Failed to initiate call. Please try again or call us directly at +1 978 830 9619."
            })
