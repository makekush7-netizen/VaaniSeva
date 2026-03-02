# VaaniSeva — Technical Q&A

*Answers verified directly from live DynamoDB + codebase on March 1, 2026*

---

## Q1: How many embeddings total in DynamoDB vectors table?

**77 embeddings** currently live in `vaaniseva-vectors`.

**Breakdown:**
- 64 knowledge items in `vaaniseva-knowledge` (32 scheme overviews + 32 FAQ sections)
- Each item generates separate embeddings for English (`text_en`) and Hindi (`text_hi`)
- 77 (not 128) because some items didn't have both language fields populated — the seeder skips empty text fields
- Each embedding is **1,024 dimensions** (Amazon Titan Embed Text v2)
- Each embedding vector is stored as a list of 1,024 Decimal values in DynamoDB

**Vector item fields:** `embedding_id`, `scheme_id`, `section_id`, `language`, `text`, `text_hi`, `embedding`

---

## Q2: What's the size of your knowledge base? (total words/KB)

| Metric | Value |
|--------|-------|
| File size | **233 KB** (238,646 bytes) |
| Total words | **21,029 words** |
| Total lines | **1,954 lines** |
| Knowledge items (DynamoDB) | **64 items** |
| Schemes covered | **32 unique government schemes** |
| Sections per scheme | **2** (overview + FAQs) |
| Languages per item | **2** (English + Hindi Devanagari) |
| Avg words per FAQ section | ~500–800 words (10+ Q&A pairs) |

**Coverage per scheme entry includes:**
- Description/overview (text_en, text_hi)
- Eligibility criteria (eligibility_en, eligibility_hi)
- How to apply (how_to_apply_en, how_to_apply_hi)
- Required documents (documents_en, documents_hi)
- Helpline number
- Official website
- 10+ detailed FAQs with step-by-step answers

---

## Q3: What exactly did the AI agent (Claude/Opus) do for ~1 hour on the data?

This refers to **Prakhyat's AI-assisted data generation work** on `seed_knowledge.py`.

**What was generated / done:**

1. **Expanded scheme count from 15 → 32** — Added 17 new government schemes:
   - Soil Health Card, PM POSHAN, Mahila Samman Savings Certificate, PM Kaushal Vikas, PM Suraksha Bima, PM Jeevan Jyoti Bima, Stand Up India, PM Matru Vandana, National Family Benefit, Samagra Shiksha, Rashtriya Bal Swasthya, PM Saubhagya, Swachh Bharat Gramin, PM Shram Yogi Mandhan, PM Vishwakarma, Janani Shishu Suraksha, PM Krishi Sinchai

2. **Created 32 detailed FAQ sections** (one per scheme) — Each FAQ has 10+ Q&A pairs covering:
   - How much money/benefit do I get?
   - Who is eligible? Who is NOT eligible?
   - What documents are needed?
   - How to apply step-by-step?
   - How to check status?
   - What to do if payment is stuck?
   - Helpline numbers and websites

3. **Translated all content to Devanagari Hindi** — Natural, simple village-level Hindi (not formal/bureaucratic)

4. **Formatted as valid Python** — Proper `SCHEMES` and `EXTRA_SECTIONS` lists with consistent field names the seeder and RAG pipeline expect

5. **Added new fields** — `category`, `how_to_apply_en/hi`, `documents_en/hi`, `website` fields (didn't exist in the original 15-scheme version)

6. **Added `local_server.py`** — A local Flask/FastAPI server for testing without Lambda deployment

**What was NOT done (still needed):**
- Marathi (`text_mr`) and Tamil (`text_ta`) translations — planned next
- Running the embeddings — that was done separately by the deploy step

---

## Q4: Current RAG Flow — When user asks "PM-Kisan scheme kya hai?", what happens step by step?

```
User speaks into phone
        │
        ▼
[1] TWILIO STT (Speech-to-Text)
    - Twilio Gather captures audio
    - Transcribes to text: "पीएम किसान योजना क्या है?"
    - Sends as POST to API Gateway with field: SpeechResult=...
        │
        ▼
[2] LAMBDA ROUTER (handler.py → lambda_handler)
    - Detects path = /voice/gather
    - Extracts: speech_text="पीएम किसान योजना क्या है?", lang="hi"
    - Calls handle_gather(params)
        │
        ▼
[3] RAG PIPELINE (handler.py → rag_pipeline)
    ├── get_embedding(speech_text)
    │       - Calls Bedrock: amazon.titan-embed-text-v2:0
    │       - Input: "पीएम किसान योजना क्या है?"
    │       - Output: list of 1,024 floats (the query vector)
    │
    ├── retrieve_context(query_embedding, language="hi")
    │       - Scans ALL 77 items from vaaniseva-vectors (DynamoDB full scan)
    │       - For each item: converts Decimal→float, computes cosine similarity
    │       - Picks TOP 3 closest matches by similarity score
    │       - Returns their text_hi fields concatenated:
    │           → "पीएम किसान योजना में किसान परिवारों को हर साल 6000 रुपये..."
    │           → "अक्सर पूछे जाने वाले प्रश्न: Q: पीएम किसान में कितने पैसे..."
    │           → (third closest match — may be related scheme)
    │
    └── ask_llm(query, context, language="hi")
            - Builds prompt with SYSTEM_PROMPT + retrieved context + user query
            - Calls Bedrock: amazon.nova-micro-v1:0
            - Returns: "पीएम किसान योजना में किसान परिवारों को हर साल ₹6000 मिलते हैं..."
        │
        ▼
[4] SARVAM TTS (handler.py → sarvam_tts)
    - Sends answer text to api.sarvam.ai/text-to-speech
    - Model: bulbul:v2, Speaker: anushka, Language: hi-IN
    - Returns WAV audio bytes
    - Uploads to S3: tts/{uuid}.wav
    - Generates 1-hour presigned URL
        │
        ▼
[5] TWILIO TWIML RESPONSE
    - Lambda returns XML:
        <Response>
          <Gather input="speech" action="/voice/gather?lang=hi">
            <Play>https://s3.presigned.url/tts/uuid.wav</Play>
          </Gather>
          <Play>goodbye.wav</Play>
        </Response>
    - Twilio plays the audio to the caller
    - Gather listens for next question → loop back to step 1
```

**Total latency:** ~4-8 seconds (Titan embed ~0.5s + DynamoDB scan ~0.5s + cosine similarity ~0.1s + Nova ~2-3s + Sarvam TTS ~1-2s)

---

## Q5: Without RAG — What would break if you removed embeddings and just sent query directly to Nova Micro?

**It would still "work" but answers would be wrong.**

### What Nova Micro knows without RAG:
Nova Micro is a small, fast model — it has general knowledge but:
- Its training cutoff means it may not know the **exact current benefit amounts** (PM-Kisan is ₹6,000/year — but schemes change)
- It doesn't know **state-specific variations** (West Bengal runs Krishak Bandhu instead of PM-Kisan)
- It doesn't know **exact document requirements** (which Khasra/Khatauni papers, exact Aadhaar linking steps)
- It doesn't know **our helpline numbers** (155261, 14555 etc.)
- It doesn't know **our specific formatting style** (phone-call brevity)
- It would likely **hallucinate** specific scheme details confidently but incorrectly

### What breaks concretely:
| Issue | Impact |
|-------|--------|
| Wrong benefit amounts | User applies expecting wrong amount |
| Missing eligibility details | Ineligible user wastes time applying |
| Wrong helpline numbers | Hallucinated numbers, user can't reach help |
| No Devanagari enforcement | Falls back to Hinglish roman script |
| Generic answers | "PM-Kisan gives financial assistance to farmers" — useless for a village caller |
| No FAQ coverage | Can't answer "my payment is stuck, what do I do?" accurately |

### What RAG actually adds:
- **Specificity:** Exact ₹6,000, exact 3 installments of ₹2,000, exact schedule (April/August/December)
- **Actionability:** "Go to pmkisan.gov.in → eKYC → enter Aadhaar → verify OTP"
- **Accuracy:** Documents required = Aadhaar + bank passbook + khatauni/khasra
- **Trust:** Real helpline 155261, real website pmkisan.gov.in
- **Scope control:** RAG context grounds Nova so it doesn't make up unrelated information

**Bottom line:** Without RAG, VaaniSeva becomes a generic AI chatbot with scheme info of uncertain accuracy. With RAG, it's a reliable, specific, actionable assistant that a villager can trust to make real decisions.
