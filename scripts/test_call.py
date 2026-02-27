# VaaniSeva - Outbound Test Call
# Usage:  python scripts/test_call.py +919876543210
#
# Twilio calls YOUR number → routes through VaaniSeva lambda
# Works from India — Twilio pays the outbound leg, not you.
# Great for judge demos too (call their number, they experience it live).

import sys
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

def make_test_call(to_number: str, api_gateway_url: str):
    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"].strip()
    )

    print(f"\nCalling {to_number}...")
    print(f"Routing through: {api_gateway_url}/voice/incoming")

    call = client.calls.create(
        to=to_number,
        from_=os.environ["TWILIO_PHONE_NUMBER"],
        url=f"{api_gateway_url}/voice/incoming",
        method="POST"
    )

    print(f"\n✅ Call initiated!")
    print(f"  Call SID : {call.sid}")
    print(f"  Status   : {call.status}")
    print(f"\nPick up your phone — VaaniSeva is calling you!")
    print(f"Track call at: https://console.twilio.com/us1/monitor/voice/calls")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/test_call.py <phone_number> <api_gateway_url>")
        print("Example: python scripts/test_call.py +919876543210 https://abc123.execute-api.us-east-1.amazonaws.com/prod")
        print("\nIf API Gateway not deployed yet, you can use ngrok:")
        print("  1. pip install pyngrok")
        print("  2. python scripts/local_server.py   (in one terminal)")
        print("  3. ngrok http 5000                  (in another terminal)")
        print("  4. Use the ngrok https URL above")
        sys.exit(1)

    to_number      = sys.argv[1]
    api_gateway_url = sys.argv[2].rstrip("/")
    make_test_call(to_number, api_gateway_url)
