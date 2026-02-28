# VaaniSeva - Local development server
# Wraps the Lambda handler in a Flask app and exposes it via ngrok.
# Usage:  python scripts/local_server.py
#
# This creates an ngrok tunnel so Twilio can reach your local machine.

import sys
import os

# Add Lambda handler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas", "call_handler"))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request
from handler import lambda_handler

app = Flask(__name__)

@app.route("/voice/<path:subpath>", methods=["GET", "POST"])
def voice_proxy(subpath):
    """Translate Flask request → Lambda event → Lambda response → Flask response."""

    # Build body from form data (Twilio sends application/x-www-form-urlencoded)
    if request.method == "POST":
        body = request.get_data(as_text=True)
    else:
        body = ""

    # Simulate API Gateway event
    event = {
        "path": f"/voice/{subpath}",
        "httpMethod": request.method,
        "body": body,
        "queryStringParameters": dict(request.args),
        "headers": dict(request.headers),
        "requestContext": {
            "domainName": request.host,
            "stage": "",  # no stage prefix for local
        },
    }

    # Call the Lambda handler
    result = lambda_handler(event, None)

    return (
        result.get("body", ""),
        result.get("statusCode", 200),
        result.get("headers", {}),
    )


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # Start ngrok tunnel
    try:
        from pyngrok import ngrok
        public_url = ngrok.connect(port, "http").public_url
        print(f"\n{'='*60}")
        print(f"  ngrok tunnel active!")
        print(f"  Public URL: {public_url}")
        print(f"{'='*60}")
        print(f"\n  Use this for your test call:")
        print(f"  python scripts/test_call.py +916232666180 {public_url}")
        print(f"\n  Or set as Twilio webhook:")
        print(f"  {public_url}/voice/incoming")
        print(f"{'='*60}\n")
    except ImportError:
        public_url = None
        print("\n⚠  pyngrok not installed — run: pip install pyngrok")
        print(f"  Starting without ngrok on http://localhost:{port}")
        print("  You can also run 'ngrok http 5000' separately.\n")

    app.run(host="0.0.0.0", port=port, debug=False)
