# VaaniSeva - Seed Script
# Run this ONCE to populate DynamoDB with government scheme data
# python scripts/seed_knowledge.py

import boto3
import json
import os
import math
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])
bedrock  = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])

knowledge_table = dynamodb.Table(os.environ["DYNAMODB_KNOWLEDGE_TABLE"])
vectors_table   = dynamodb.Table(os.environ["DYNAMODB_VECTORS_TABLE"])

# ── Scheme data ───────────────────────────────────────────────
SCHEMES = [
    {
        "scheme_id": "pm-kisan",
        "section_id": "overview",
        "name_en": "PM-Kisan",
        "name_hi": "पीएम किसान",
        "text_en": "PM-Kisan gives Rs 6000 per year directly to farmer families. The money comes in 3 payments of Rs 2000 each. Any farmer who owns farmland can apply.",
        "text_hi": "पीएम किसान योजना में किसान परिवारों को हर साल 6000 रुपये मिलते हैं। यह पैसा 2000-2000 रुपये की तीन किस्तों में आता है। जिस किसान के पास खेती की जमीन है, वो आवेदन कर सकता है।",
        "eligibility_en": "Farmer families who own cultivable land. Not available for income tax payers, government employees, or professionals.",
        "eligibility_hi": "जिन किसान परिवारों के पास खेती योग्य जमीन हो। आयकर देने वाले, सरकारी कर्मचारी और पेशेवरों को नहीं मिलेगी।",
        "how_to_apply_en": "Visit nearest CSC center or pmkisan.gov.in with Aadhaar card, bank passbook, and land documents.",
        "helpline": "155261",
        "website": "pmkisan.gov.in"
    },
    {
        "scheme_id": "ayushman-bharat",
        "section_id": "overview",
        "name_en": "Ayushman Bharat",
        "name_hi": "आयुष्मान भारत",
        "text_en": "Ayushman Bharat gives free health insurance of Rs 5 lakh per year to poor families. You can get free treatment at government and empanelled private hospitals.",
        "text_hi": "आयुष्मान भारत योजना गरीब परिवारों को हर साल 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा देती है। सरकारी और सूचीबद्ध निजी अस्पतालों में मुफ्त इलाज मिलता है।",
        "eligibility_en": "Families listed in SECC 2011 data. Includes daily wage workers, construction workers, domestic workers. Check eligibility at mera.pmjay.gov.in",
        "eligibility_hi": "SECC 2011 सूची में शामिल परिवार। दैनिक मजदूर, निर्माण कार्यकर्ता, घरेलू कामगार शामिल हैं। mera.pmjay.gov.in पर जांचें।",
        "how_to_apply_en": "Visit nearest Ayushman Bharat empanelled hospital or CSC with Aadhaar. No registration needed if already listed.",
        "helpline": "14555",
        "website": "pmjay.gov.in"
    },
    {
        "scheme_id": "mgnrega",
        "section_id": "overview",
        "name_en": "MGNREGA",
        "name_hi": "मनरेगा",
        "text_en": "MGNREGA guarantees 100 days of paid work per year to rural families. The daily wage is around Rs 200-300 depending on your state. Any adult in a rural household can apply.",
        "text_hi": "मनरेगा ग्रामीण परिवारों को साल में 100 दिन काम की गारंटी देती है। राज्य के अनुसार रोज 200-300 रुपये मजदूरी मिलती है। ग्रामीण घर का कोई भी वयस्क आवेदन कर सकता है।",
        "eligibility_en": "Any adult member of a rural household willing to do unskilled manual work. Apply at the local gram panchayat office.",
        "eligibility_hi": "ग्रामीण घर का कोई भी वयस्क सदस्य जो अकुशल शारीरिक काम करने को तैयार हो। स्थानीय ग्राम पंचायत में आवेदन करें।",
        "how_to_apply_en": "Go to your gram panchayat office with Aadhaar and bank account details. You will get a job card within 15 days.",
        "helpline": "1800-111-555",
        "website": "nrega.nic.in"
    },
    {
        "scheme_id": "pm-awas-yojana",
        "section_id": "overview",
        "name_en": "PM Awas Yojana",
        "name_hi": "पीएम आवास योजना",
        "text_en": "PM Awas Yojana gives money to build or improve homes for poor families. Rural families can get up to Rs 1.2 lakh and urban families can get home loan subsidy.",
        "text_hi": "पीएम आवास योजना गरीब परिवारों को घर बनाने या सुधारने के लिए पैसे देती है। ग्रामीण परिवारों को 1.2 लाख रुपये तक मिल सकते हैं और शहरी परिवारों को होम लोन सब्सिडी मिलती है।",
        "eligibility_en": "Families without pucca house, EWS/LIG income groups. Not for families who already own a pucca house anywhere in India.",
        "eligibility_hi": "जिन परिवारों के पास पक्का मकान नहीं है, EWS/LIG आय वर्ग। जिनके पास पहले से पक्का मकान हो, उन्हें नहीं मिलेगा।",
        "how_to_apply_en": "Apply at gram panchayat (rural) or urban local body office with Aadhaar, income certificate, and bank details.",
        "helpline": "1800-11-6163",
        "website": "pmaymis.gov.in"
    },
    {
        "scheme_id": "sukanya-samriddhi",
        "section_id": "overview",
        "name_en": "Sukanya Samriddhi Yojana",
        "name_hi": "सुकन्या समृद्धि योजना",
        "text_en": "Sukanya Samriddhi is a savings scheme for girl children. You deposit money and get high interest. The money can be used for her education or marriage after she turns 18.",
        "text_hi": "सुकन्या समृद्धि बेटियों के लिए बचत योजना है। पैसे जमा करने पर अच्छा ब्याज मिलता है। 18 साल बाद यह पैसा उसकी पढ़ाई या शादी में काम आता है।",
        "eligibility_en": "Any girl child below 10 years of age. Account opened by parent or guardian at post office or bank.",
        "eligibility_hi": "10 साल से कम उम्र की कोई भी बेटी। माता-पिता या अभिभावक पोस्ट ऑफिस या बैंक में खाता खोल सकते हैं।",
        "how_to_apply_en": "Visit nearest post office or bank with girl's birth certificate, parent Aadhaar, and address proof. Minimum deposit Rs 250.",
        "helpline": "1800-266-6868",
        "website": "nari.nic.in"
    }
]


def get_embedding(text: str) -> list:
    response = bedrock.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json"
    )
    result = json.loads(response["body"].read())
    return result["embedding"]


def seed():
    print("Seeding knowledge base...")
    for scheme in SCHEMES:
        # Save to knowledge table
        knowledge_table.put_item(Item=scheme)
        print(f"  ✓ Knowledge: {scheme['scheme_id']}")

        # Generate embeddings for English and Hindi text, save to vectors table
        for lang in ["en", "hi"]:
            text_key = f"text_{lang}"
            text = scheme.get(text_key, "")
            if not text:
                continue

            print(f"    Generating embedding for {scheme['scheme_id']} ({lang})...")
            embedding = get_embedding(text)

            vectors_table.put_item(Item={
                "embedding_id": f"{scheme['scheme_id']}#{lang}",
                "scheme_id": scheme["scheme_id"],
                "section_id": scheme["section_id"],
                "language": lang,
                "text": text,
                f"text_{lang}": text,
                "embedding": embedding
            })
            print(f"    ✓ Vector stored: {scheme['scheme_id']} ({lang})")

    print("\nDone! Knowledge base seeded with 5 schemes.")


if __name__ == "__main__":
    seed()
