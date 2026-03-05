"""
Seed Task 1C entries only — Emergency Helplines, Medical Emergencies, Legal Rights, MSP, KCC.
Run: python scripts/seed_task1c.py
"""
import os, json, sys
import boto3
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION = os.environ.get("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION,
                           aws_access_key_id=AWS_KEY,
                           aws_secret_access_key=AWS_SECRET)
bedrock  = boto3.client("bedrock-runtime", region_name=REGION,
                         aws_access_key_id=AWS_KEY,
                         aws_secret_access_key=AWS_SECRET)

KNOWLEDGE_TABLE = os.environ.get("DYNAMODB_KNOWLEDGE_TABLE", "vaaniseva-knowledge")
VECTORS_TABLE   = os.environ.get("DYNAMODB_VECTORS_TABLE", "vaaniseva-vectors")
EMBEDDING_MODEL = os.environ.get("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

knowledge_table = dynamodb.Table(KNOWLEDGE_TABLE)
vectors_table   = dynamodb.Table(VECTORS_TABLE)

TASK1C_IDS = {
    "emergency-helplines",
    "medical-emergency-heart-attack",
    "medical-emergency-snake-bite",
    "medical-emergency-child-fever",
    "medical-emergency-drowning-choking",
    "legal-rights-domestic-violence",
    "legal-rights-arrested",
    "free-legal-aid-india",
    "rti-right-to-information",
    "msp-minimum-support-price",
    "kisan-credit-card",
}


def get_embedding(text: str) -> list:
    response = bedrock.invoke_model(
        modelId=EMBEDDING_MODEL,
        body=json.dumps({"inputText": text[:8000]}),  # Titan has 8k token limit
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def seed_items(items):
    for item in items:
        sid = item["scheme_id"]
        sec = item.get("section_id", "overview")

        # Save to knowledge table
        knowledge_table.put_item(Item=item)
        print(f"  ✓ Knowledge: {sid} / {sec}")

        # Generate embedding for each language
        for lang in ["en", "hi", "mr", "ta"]:
            text = item.get(f"text_{lang}", "")
            if not text:
                continue

            print(f"    Generating embedding for {sid}#{sec} ({lang})...", flush=True)
            try:
                embedding = [Decimal(str(round(v, 8))) for v in get_embedding(text)]
                vectors_table.put_item(Item={
                    "embedding_id": f"{sid}#{sec}#{lang}",
                    "scheme_id": sid,
                    "section_id": sec,
                    "language": lang,
                    "text": text,
                    f"text_{lang}": text,
                    "embedding": embedding,
                    "category": item.get("category", "general"),
                })
                print(f"    ✓ Vector: {sid}#{sec} ({lang})")
            except Exception as e:
                print(f"    ✗ Embedding failed for {sid}#{sec} ({lang}): {e}")


if __name__ == "__main__":
    # Load the full seed data by exec-ing seed_knowledge.py
    src_path = os.path.join(os.path.dirname(__file__), "seed_knowledge.py")
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()

    ns = {}
    # Prevent seed() from executing automatically
    patched = src.replace('if __name__ == "__main__":', 'if False and __name__ == "__main__":')
    exec(compile(patched, "seed_knowledge.py", "exec"), ns)

    all_items = ns.get("SCHEMES", []) + ns.get("EXTRA_SECTIONS", [])
    task1c_items = [i for i in all_items if i.get("scheme_id") in TASK1C_IDS]

    print(f"Found {len(task1c_items)} Task 1C items to seed:\n")
    for i in task1c_items:
        print(f"  - {i['scheme_id']} / {i.get('section_id')}")

    print(f"\nStarting seed of {len(task1c_items)} items...")
    seed_items(task1c_items)
    print(f"\n✅ Done! Seeded {len(task1c_items)} Task 1C entries.")
