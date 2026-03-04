# VaaniSeva — Product Requirements Document
### Version 2.0 · March 2026 · AI for Bharat Hackathon Build

---

## What VaaniSeva Actually Is

VaaniSeva (वाणीसेवा, meaning "Voice Service") is a phone-first AI assistant built specifically for the 440 million Indians who have a basic mobile phone but are locked out of the AI revolution because it requires a smartphone, internet data, and English literacy. VaaniSeva turns any ₹1,200 "dabba" feature phone or basic Android into a gateway to expert-level knowledge — simply by calling a number. A farmer in Vidarbha can ask in his own dialect which crop to plant this week given last night's rainfall, hear the current mandi price for wheat in his district, find out if his family qualifies for PM-Kisan, and talk through the anxiety of a failed harvest — all in one call, in his own language, without touching a screen. VaaniSeva is not a government IVR bot. It is not an FAQ system. It is the smartest, most patient, most knowledgeable friend that rural India — and increasingly lonely urban India — has ever had access to. The core infrastructure is voice-in, voice-out: a caller speaks naturally, the system transcribes it, retrieves verified knowledge, reasons over it with a large language model, and speaks the answer back — end to end in under 4 seconds. Every piece of information in critical domains (healthcare, legal rights, emergency contacts) is verified by human professionals and AI review agents before it enters the system, so the assistant never hallucinates a wrong helpline number to someone in crisis. This is the product. Everything else in this document is the plan to build it right.

---

## Table of Contents

1. [Core Architecture](#1-core-architecture)
2. [Language & Voice Stack](#2-language--voice-stack)
3. [Knowledge System — Verified RAG](#3-knowledge-system--verified-rag)
4. [Real-Time Data Integrations](#4-real-time-data-integrations)
5. [Personality & LLM Selection](#5-personality--llm-selection)
6. [Emotional Intelligence & Mental Health System](#6-emotional-intelligence--mental-health-system)
7. [Safety — Authority Alerting](#7-safety--authority-alerting)
8. [User Accounts & Tiers](#8-user-accounts--tiers)
9. [B2B2C Monetization](#9-b2b2c-monetization)
10. [Technical Implementation Plan](#10-technical-implementation-plan)
11. [Pitch & Demo Strategy](#11-pitch--demo-strategy)
12. [Future Roadmap](#12-future-roadmap)

---

## 1. Core Architecture

### Current State (Deployed)
```
Caller → Twilio (STT) → API Gateway → Lambda (handler.py)
                                          ↓
                              Bedrock Titan Embed → DynamoDB RAG
                                          ↓
                              OpenAI GPT-4o-mini (primary)
                              Amazon Bedrock Nova Micro (fallback)
                                          ↓
                              Sarvam AI TTS → S3 → Twilio plays audio
```

### Target Architecture (v2)
```
Caller → Twilio (STT, multi-lang) → API Gateway → Lambda
                                                      ↓
                                          ┌─────────────────────┐
                                          │   Request Router    │
                                          │  (intent + safety)  │
                                          └──────────┬──────────┘
                                                     ↓
                              ┌──────────────────────────────────────┐
                              │           Knowledge Layer            │
                              │  Verified RAG (DynamoDB vectors)     │
                              │  Real-time APIs (mandi, weather)     │
                              │  Agmarknet · IMD · PM portal APIs    │
                              └──────────────────┬───────────────────┘
                                                 ↓
                              ┌──────────────────────────────────────┐
                              │           LLM Layer                  │
                              │  Personality-tuned system prompt     │
                              │  Conversation memory (DynamoDB)      │
                              │  Emotion state tracking              │
                              └──────────────────┬───────────────────┘
                                                 ↓
                              ┌──────────────────────────────────────┐
                              │        Safety & Flagging Layer       │
                              │  Crisis detection → escalation       │
                              │  Depression scoring (multi-call)     │
                              │  Authority alert system              │
                              └──────────────────┬───────────────────┘
                                                 ↓
                              Sarvam TTS (per-language voice) → S3 → Caller
```

---

## 2. Language & Voice Stack

### Current (Working)
| Language | Code | Sarvam Speaker | Twilio STT |
|---|---|---|---|
| Hindi | hi-IN | anushka | hi-IN |
| Marathi | mr-IN | manisha | mr-IN |
| Tamil | ta-IN | vidya | ta-IN |
| English | en-IN | arya | en-IN |

### Bhashini Integration — Decision
**Status: Deferred for hackathon.** Bhashini's API is not yet available under the "AI for Bharat" hackathon free tier. Their platform (bhashini.gov.in/ulca) requires a registered organization account and approval pipeline that takes weeks. For the hackathon:
- **Use Sarvam AI for TTS** (currently working, 4 languages)
- **Use Twilio Gather for STT** (built-in, reliable, no extra cost)
- **Mention Bhashini in the pitch** as the planned integration for production scale (22 scheduled languages via a single government API + political goodwill from judges)

Pitch Framing: *"We've architected the system so Bhashini drops in as a translation layer — our voice pipeline is provider-agnostic. For this demo we use Sarvam AI, which covers our primary 4 languages."*

### Phase 2 Language Expansion
Add Telugu, Kannada, Bengali via Sarvam (all on `bulbul:v2`). Bhojpuri support via Hindi model (Sarvam handles dialect tolerance reasonably well — critical for demo believability).

---

## 3. Knowledge System — Verified RAG

### The Problem with Raw LLM Answers
When someone in a medical emergency asks for the nearest PHC or a domestic violence survivor asks for a shelter helpline, a hallucinated phone number is worse than no answer. The LLM cannot be trusted to pull accurate, current contact information from its training data.

### The Verified RAG Solution

**Principle:** Everything in the vector database has gone through a 3-stage review before it can ever be spoken to a user.

#### Review Pipeline
```
Stage 1: AI Agent Review (automated, runs nightly)
  - Bedrock Claude checks every entry for factual consistency
  - Flags entries where phone numbers, amounts, dates appear
  - Checks if eligibility criteria match official govt website text
  - Output: PASS / FLAGGED / NEEDS_HUMAN

Stage 2: Human Expert Review (for FLAGGED items)
  - Domain experts by category:
    · Healthcare: empaneled MBBS doctor or ASHA supervisor
    · Legal: enrolled advocate or legal aid volunteer
    · Agriculture: KVK (Krishi Vigyan Kendra) officer
    · Finance: RBI-empaneled financial literacy trainer
  - Each reviewer gets a simple Approve/Edit/Reject interface (web form)
  - Once approved: entry is marked verified=true, reviewer_id stored

Stage 3: Expiry & Drift Detection (scheduled Lambda, weekly)
  - Crawls official government URLs stored alongside each entry
  - Compares against live page content using diff + embedding similarity
  - If drift detected: auto-flag for Stage 2 re-review
  - Helpline numbers: called via a test Twilio outbound call monthly
    (a 1-ring test — if it connects, it's active)
```

#### Knowledge Categories & Fields in DynamoDB
```python
{
  "scheme_id": "pm_kisan_001",
  "category": "agriculture_scheme",      # for routing
  "subcategory": "income_support",
  "verified": True,
  "verified_by": "reviewer_id_xyz",
  "verified_at": 1741200000,
  "expires_at": 1772736000,              # force re-review annually
  "source_url": "https://pmkisan.gov.in",

  # Text in each language (for RAG retrieval priority)
  "text_hi": "...",    # Hindi Devanagari
  "text_mr": "...",    # Marathi
  "text_ta": "...",    # Tamil
  "text_en": "...",    # English

  # Structured fast-lookup fields (bypasses LLM for critical info)
  "helpline_numbers": ["155261", "1800115526"],
  "eligibility_summary": "...",
  "documents_required": ["Aadhaar", "Land record", "Bank passbook"],
  "apply_url": "https://pmkisan.gov.in/registrationform.aspx",

  # Embedding for vector search
  "embedding": [...]
}
```

#### Critical Information Lock
For fields like `helpline_numbers`, `apply_url`, and `documents_required` — the LLM is **not allowed to generate these from scratch**. The system injects them directly into the TTS response template:

```python
# In ask_llm(), before calling GPT:
if structured_data.get("helpline_numbers"):
    # Append verified helpline AFTER LLM response, not generated by LLM
    verified_suffix = f"हेल्पलाइन नंबर है: {structured_data['helpline_numbers'][0]}"
    llm_answer = llm_answer + " " + verified_suffix
```

This means: the LLM can be creative and conversational about context, but critical contact information always comes from the verified database, never hallucinated.

---

## 4. Real-Time Data Integrations

### 4.1 Mandi (Agricultural Market) Prices

**Source:** Agmarknet API (data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)
- Free, official Government of India dataset
- Updated daily at approximately 10 AM
- Covers 3,000+ mandis, 300+ commodities

**Implementation:**
```python
# scripts/fetch_mandi_prices.py — runs as scheduled EventBridge Lambda, daily
import requests

def fetch_mandi_price(commodity: str, state: str, district: str) -> dict:
    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": os.environ["DATA_GOV_API_KEY"],
        "format": "json",
        "filters[commodity]": commodity,
        "filters[state]": state,
        "filters[district]": district,
        "limit": 5
    }
    r = requests.get(url, params=params, timeout=5)
    records = r.json().get("records", [])
    # Returns modal_price, min_price, max_price, market_name
    return records
```

**In handler:** When the user's query is classified as a price query (via intent detection), the Lambda calls Agmarknet directly, bypasses RAG, formats the result, and speaks it. No LLM hallucination possible — it's live data.

**Demo Script:** *"Aaj Varanasi mandi mein gehu ka bhaav kya hai?"* → VaaniSeva fetches live, responds *"आज वाराणसी मंडी में गेहूँ का भाव ₹2,340 प्रति क्विंटल है। अधिकतम ₹2,380 और न्यूनतम ₹2,300 चल रहा है।"*

### 4.2 Weather

**Source:** IMD (India Meteorological Department) API + OpenWeatherMap free tier as fallback
- 5-day forecast available free
- District-level granularity

**Use Case:** Farmer asks "kya kal baarish hogi?" → fetches district weather by asking which district they're in (or from their profile if registered).

### 4.3 Government Portal Status Checks

**PM-Kisan Payment Status:** `pmkisan.gov.in` API (unofficial but stable endpoint, widely used)
- Input: Aadhaar or registration number
- Output: payment installment status

**Ayushman Bharat Eligibility:** `pmjay.gov.in/is-eligible` API
- Input: mobile number or Ration Card number
- Output: eligible / not eligible + family card status

These are injected as **agentic tool calls** — the LLM decides when to call them, uses function calling / tool use pattern.

### 4.4 Data Freshness Strategy
- Mandi prices: fetched live on every relevant query (cached 30 min in Lambda memory)
- Weather: cached 1 hour
- Government eligibility: not cached (real-time, user-specific)
- Knowledge base: weekly automated drift check + nightly AI review

---

## 5. Personality & LLM Selection

### The Problem
Amazon Bedrock Nova Micro (current fallback) is optimized for speed and cost, not warmth. Even GPT-4o-mini can sound robotic if the prompt doesn't actively fight it. The voice interface makes robotic responses feel even worse — there's no visual distraction.

### LLM Options Available on AWS Bedrock (India-region compatible, UPI payment)
| Model | Warmth | Speed | Cost/1K tokens | Notes |
|---|---|---|---|---|
| Claude 3 Haiku | ⭐⭐⭐⭐ | Fast | $0.00025 | Needs real card, ruled out |
| Claude 3.5 Haiku | ⭐⭐⭐⭐⭐ | Fast | $0.0008 | Same issue |
| Llama 3.1 8B Instruct | ⭐⭐⭐ | Very fast | $0.00022 | Available on Bedrock, UPI ok |
| Llama 3.3 70B Instruct | ⭐⭐⭐⭐ | Medium | $0.00072 | More personality, Bedrock |
| Mistral 7B Instruct | ⭐⭐⭐ | Fast | $0.00015 | Less Hindi quality |
| Amazon Nova Pro | ⭐⭐⭐ | Fast | $0.0008 | Good Hindi, flat tone |
| **OpenAI GPT-4o-mini** | ⭐⭐⭐⭐ | Fast | $0.00015 | **Current primary, needs card** |
| **OpenAI GPT-4o** | ⭐⭐⭐⭐⭐ | Medium | $0.0025 | Best personality, needs card |

**Recommendation:**
- For hackathon: Use **Llama 3.3 70B on Bedrock** as the primary (UPI-compatible, strong Hindi, much more personality than Nova Micro)
- For production: OpenAI GPT-4o with Llama 3.3 as fallback
- Switch by changing `LLM_PROVIDER` + model ID in `.env`

### Personality Engineering (Prompt Level)
Beyond model choice, these prompt techniques make a significant difference:

**1. Named identity reinforcement:** VaaniSeva refers to itself by name, never as "the assistant" or "the AI."

**2. Emotional mirroring cues:** Explicit instructions to match the caller's energy level.

**3. Regional vocabulary seeding:** Seed the system prompt with common rural vocabulary so the model doesn't default to urban register Hindi.

**4. Conversation arc awareness:** The model knows it's in a phone call with turns — it should not dump 5 facts at once, but tease one fact and invite a follow-up.

**5. Filler naturalness:** Explicit instruction to use natural fillers: "अच्छा, तो सुनिए...", "हाँ, बिल्कुल...", "अरे, यह तो बहुत अच्छा सवाल है" — so the caller doesn't feel they're talking to a search engine.

**Implementation:** These are already partially in the current SYSTEM_PROMPT. The gap is the model — Llama 3.3 70B will follow these instructions significantly better than Nova Micro.

---

## 6. Emotional Intelligence & Mental Health System

### 6.1 The Problem of False Positives

Depression detection on a single call is dangerous — a teenager pranking the system, someone venting after a bad day, or a user with a naturally melancholic communication style would all trigger a naive classifier. We need multi-signal, multi-call scoring.

### 6.2 Emotion Detection Architecture

**Signal Layer (per turn, in Lambda):**
```python
DISTRESS_SIGNALS = {
    "lexical": [
        "मरना चाहता हूं", "जीना नहीं चाहता", "बहुत थक गया हूं जिंदगी से",
        "koi fayda nahi", "want to die", "can't go on",
        "आत्महत्या", "suicide", "end it all"
    ],
    "contextual_themes": [
        "financial ruin + hopelessness",
        "family abandonment",
        "crop failure + debt + no support"
    ]
}
```

**Scoring Model (stored per call_sid in DynamoDB):**
```python
{
  "call_sid": "...",
  "phone_number_hash": "sha256(+91XXXXXXXXXX)",  # hashed, not raw
  "call_history": [
    {
      "date": "2026-03-04",
      "distress_score": 0.3,    # 0-1, per call
      "themes_detected": ["financial_stress"],
      "escalated": False
    }
  ],
  "cumulative_score": 0.3,
  "consecutive_distress_calls": 1,
  "flagged_for_review": False
}
```

**Escalation Threshold Logic:**
```
Single call, score > 0.85 (explicit suicidal language) → Immediate
Single call, score > 0.6 → Suggest helpline in-call
3+ consecutive calls with score > 0.4 → Flag for human review
Cumulative score > 2.0 over 7 days → Mark as "persistent distress"
```

**The Prank Filter:**
- Account age < 7 days + single call + score 0.6-0.8 → Do NOT escalate, only suggest helpline
- If the same number has called 10+ times with no prior distress → discount single spike by 40%
- Voice of a child/teen (Sarvam can infer from audio characteristics) + distress → reduce score weight, still suggest helpline but note age-profile
- Rapid topic switching in the same call (asked about cricket, schemes, suddenly suicidal) → score weighted down by 30%

### 6.3 In-Call Mental Health Response

When distress is detected, the LLM is instructed to shift tone:
```
INJECTED INTO SYSTEM PROMPT MID-CALL:
"The caller appears to be in emotional distress. Do NOT continue with information.
Pause the normal conversation. Acknowledge what they said with genuine warmth.
Ask them: are they safe right now? Mention iCall (9152987821) and
Vandrevala Foundation (1860-2662-345) naturally in conversation, not as a list.
Do not abruptly end the call. Be present."
```

### 6.4 Post-Call Alert System

For persistent distress cases (not single-call pranks):
```python
def send_alert(phone_hash: str, distress_profile: dict):
    # Option 1: SMS to the iCall case management number
    # (requires iCall API partnership — Phase 2)

    # Option 2: Internal dashboard flag for human volunteer callback
    # A VaaniSeva volunteer calls the user the next day
    # "Hum VaaniSeva se bol rahe hain — kal aap ne baat ki thi..."

    # Option 3: SNS notification to registered NGO partner
    sns.publish(
        TopicArn=os.environ["ALERT_TOPIC_ARN"],
        Message=json.dumps({
            "type": "persistent_distress",
            "phone_hash": phone_hash,
            "call_count": distress_profile["consecutive_distress_calls"],
            "themes": distress_profile["themes_detected"],
            "last_call_date": distress_profile["last_call_date"]
        })
    )
```

**Privacy Note:** Phone numbers are stored only as SHA-256 hashes. The raw number is never stored in the distress table. The volunteer callback works because Twilio holds the mapping.

---

## 7. Safety — Authority Alerting

### Suspicious Activity Detection

Beyond mental health, VaaniSeva may receive calls describing:
- Child abuse / domestic violence in progress
- Caste violence or threats
- Public health emergencies (multiple callers from same area describing same illness)

**Implementation:**
```python
AUTHORITY_TRIGGERS = {
    "immediate_danger": {
        "keywords": ["maar rahe hain", "abhi ho raha hai", "bachao", "help police"],
        "action": "suggest_100_immediately"
    },
    "child_in_danger": {
        "keywords": ["bachche ko maar raha", "child abuse", "बच्चे के साथ"],
        "action": "suggest_1098_childline"
    },
    "domestic_violence": {
        "keywords": ["pati maar raha", "ghar mein maar", "mahila"],
        "action": "suggest_181_womenhelpline"
    }
}
```

For immediate danger: the LLM is paused entirely. A hardcoded TTS response plays: *"कृपया तुरंत 100 पर कॉल करें। मैं आपके साथ हूं।"*

**Cluster Detection (future):** If 5+ calls from the same PIN code district mention fever/vomiting/illness within 6 hours → trigger SNS alert to district CMHO (Chief Medical and Health Officer) contact. Epidemiological early warning system built on top of a phone line.

---

## 8. User Accounts & Tiers

### Tier 0 — Anonymous Free (No Registration)
- Daily limit: **10 minutes per phone number** (tracked by caller ID hash)
- No conversation history between calls (memory is per-call only)
- No personalization
- Full access to all knowledge domains
- When limit is hit: *"आपका आज का 10 मिनट का फ्री टाइम खत्म हो गया। कल फिर कॉल करें। या VaaniSeva Pro के लिए vaaniseva.in पर जाएं।"*

### Tier 1 — Registered Free
- Register via SMS/WhatsApp (one-time OTP, no app needed)
- Daily limit: **20 minutes**  
- Conversation summary stored — next call starts with: *"नमस्ते [नाम]! कल आप पीएम किसान की बात कर रहे थे — क्या आपको आवेदन हो गया?"*
- Stored preferences: language, district, crop type (for agriculture queries)

### Tier 2 — VaaniSeva Pro (₹49/month)
- **Unlimited minutes**
- Full conversation history across calls
- Addressed by name every call
- Proactive callbacks: scheduled reminders (*"आपकी फसल बीमा की आखिरी तारीख 30 जून है — आवेदन हो गया?"*)
- Priority LLM routing (GPT-4o instead of GPT-4o-mini if available)
- Mandi price alerts (SMS when price crosses user-set threshold)
- Weather alerts (before frost/rain in their district)

### Tier 3 — Institutional (B2B)
- NGOs, SHGs, Panchayats, KVK offices
- Per-seat pricing or bulk minute bundles
- Custom knowledge injection (their local schemes, contacts, programs)
- Call analytics dashboard (what are their members asking about?)
- API access for their own apps/websites

### Account Storage Schema
```python
# DynamoDB: vaaniseva-users table
{
  "phone_hash": "sha256(+91..)",     # partition key, never raw number
  "user_id": "usr_xxxx",
  "name": "Ramesh",                  # optional, user-provided
  "language_pref": "hi",
  "district": "Nashik",
  "state": "Maharashtra",
  "tier": "free_registered",
  "daily_seconds_used": 423,
  "daily_reset_date": "2026-03-04",
  "total_calls": 7,
  "registered_at": 1741200000,
  "preferences": {
    "crops": ["wheat", "onion"],
    "favorite_topics": ["pm_kisan", "weather"]
  },
  "distress_profile": {
    "cumulative_score": 0.0,
    "consecutive_distress_calls": 0,
    "flagged": False
  }
}
```

---

## 9. B2B2C Monetization

### For Hackathon Pitch — Remove Direct Consumer Charge
Do not present ₹49/month as the primary business model to judges. Instead:

**Revenue Stream 1: Government SLA Contract**
Government currently spends ₹800-1,200 per citizen grievance resolved via call centers. VaaniSeva resolves the same query for ₹0.80 (compute + Twilio cost). Pitch this as a 1,000x efficiency gain. Target: state government digital mission (e.g., MahaIT, Tamil Nadu e-Governance) as a bulk subscriber paying per resolved query or per toll-free minute.

**Revenue Stream 2: CSR / Foundation Grants**
Gates Foundation, Tata Trusts, Azim Premji Foundation all fund "last-mile digital access" projects. VaaniSeva's impact metrics (queries answered / correct helpline referrals / distress interventions) are exactly the KPIs these funders track.

**Revenue Stream 3: Affiliate (Done Responsibly)**
NOT "any brand pays for mentions." Instead: VaaniSeva partners only with IRDAI-registered insurance companies and NABARD-approved microfinance institutions. When a user asks about crop insurance, VaaniSeva provides verified information about PM Fasal Bima, then voluntarily mentions: *"एक सरकारी-मान्यता प्राप्त ICICI Lombard का प्लान भी है जिसमें ज़्यादा कवरेज मिलती है — चाहें तो उनका नंबर दूं?"* The referral is transparent, opt-in, and the partner is vetted.

**Revenue Stream 4: Pro Subscriptions (Urban)**
Position for urban users not as "loneliness bot" (too niche) but as:
*"Eyes-Free AI for Busy Professionals"* — driving to work, cooking, managing elderly parents remotely. "Tell me what my mother asked VaaniSeva about her blood pressure medication" becomes a dashboard feature for adult children who've set up VaaniSeva for their parents.

---

## 10. Technical Implementation Plan

### Phase 1 — Hackathon Submission (Now → Demo Day)
**Priority: Make the demo call jaw-dropping. Nothing else matters.**

| Task | Owner | Time |
|---|---|---|
| Switch Bedrock model to Llama 3.3 70B | Dev | 1 hour |
| Add Agmarknet API for live mandi prices | Dev | 3 hours |
| Add intent classifier (price / scheme / health / emotional) | Dev | 2 hours |
| Hardcode distress trigger → immediate helpline response | Dev | 1 hour |
| Record Bhojpuri demo call script | Team | 2 hours |
| Prepare pitch deck with "Voice-First OS" framing | Team | 1 day |
| Add user daily limit tracking (10 min free) | Dev | 2 hours |
| Deploy all + smoke test 5 calls | Dev | 1 hour |

### Phase 2 — Post-Hackathon (Month 1-2)
- Verified RAG pipeline with human review interface
- Agmarknet + IMD weather integration (full)
- User account registration via SMS OTP
- Conversation memory across calls (registered users)
- Emotion scoring per call + DynamoDB distress profile
- Volunteer callback system for flagged users

### Phase 3 — Production (Month 3-6)
- Bhashini integration (when their API access opens)
- PM-Kisan status check agentic tool call
- Ayushman Bharat eligibility tool call
- Pro tier billing via Razorpay
- Institutional dashboard (call analytics for NGOs)
- iCall API partnership for distress escalation
- WhatsApp Bot (same brain, Twilio WhatsApp sandbox)

### Phase 4 — Scale (Month 6-12)
- Voice biometric auth (Sarvam has this capability)
- Outbound proactive calls (reminders, price alerts, scheme deadlines)
- District-level health cluster detection (epidemiological alerts)
- Regional language expansion: Telugu, Kannada, Bengali
- UMANG API integration (government form filling via voice)

---

## 11. Pitch & Demo Strategy

### The 30-Second Elevator Pitch
*"India has 700 million phone users. 440 million of them can't access ChatGPT because it requires English, a smartphone, and data. VaaniSeva gives them the same intelligence through a phone call. A farmer speaks in Bhojpuri. We understand. We answer — in 4 seconds, in his language, with verified information from government sources and live mandi prices. We are not building an app for the top 10%. We are building the Voice-First Operating System for the other 90%."*

### The Demo Call (Practice This 20 Times)
**Script:**
1. Call the VaaniSeva number live on stage
2. Press 1 for Hindi
3. Ask (in Bhojpuri accent Hindi): *"hum ke batao bhaiya, aaj Varanasi mandi mein lahsun ka bhaav kya chal raha hai, aur kya PM Kisan ke liye apply ho sakta hai mere gaon mein"*
4. VaaniSeva responds: Live garlic price from Agmarknet + PM-Kisan eligibility criteria in simple Hindi
5. Follow-up: *"Meri beti ki padhai ke liye koi scholarship hai?"* → VaaniSeva answers from RAG, mentions National Scholarship Portal

**Why this works:** It answers 3 different question types (real-time data, scheme eligibility, education) in one fluid conversation. Judges see memory, live data, and multilingual RAG — all in 90 seconds.

### Architecture Diagram for Slides
```
[ ₹1,200 Phone ] ──calls──→ [ Toll-Free Number ]
                                      ↓
                          [ Twilio Voice Gateway ]
                                      ↓
                 ┌────────────────────────────────┐
                 │        VaaniSeva Brain         │
                 │  ┌─────────┐  ┌─────────────┐ │
                 │  │ Sarvam  │  │  GPT-4o /   │ │
                 │  │  STT    │  │  Llama 3.3  │ │
                 │  └─────────┘  └─────────────┘ │
                 │  ┌──────────────────────────┐  │
                 │  │  Verified Knowledge RAG  │  │
                 │  │  + Live APIs (Agmarknet) │  │
                 │  └──────────────────────────┘  │
                 └────────────────────────────────┘
                                      ↓
                          [ Sarvam AI TTS — 4 Languages ]
                                      ↓
                          [ Answer in < 4 seconds ]
```

---

## 12. Future Roadmap (Placeholder — Not for Hackathon)

### Customizable Personal Agent (Pro Max Tier)
Users can set:
- Agent name (e.g., "Meena" instead of "VaaniSeva")
- Personality style (formal / friendly / elder-style respectful)
- Voice selection from available Sarvam speakers
- Preferred language mix (pure Hindi vs Hindi-English mix)
- Model preference (if exposed via API — Llama vs GPT, etc.)
This is architecturally straightforward (all parameters stored in user profile, injected into SYSTEM_PROMPT and `LANG_CONFIG` per call) but adds UX complexity for configuration. Deferred to post-Series A.

### WhatsApp Integration
Same Lambda brain, Twilio WhatsApp Business API as the transport. Text-only (no TTS/STT). Advantages: async, searchable, shareable. Disadvantages: loses the "no smartphone needed" pitch.

### UMANG API — Form Filling by Voice
User says: *"मेरे लिए PM-Kisan register कर दो"*. VaaniSeva collects Aadhaar, land details, bank details over voice, then submits the UMANG API form on their behalf. True agentic workflow. Requires UMANG API access (government partnership needed).

### Proactive Outbound Calls
Scheduled Lambda calls registered users:
- 7 days before application deadlines for schemes they've expressed interest in
- Day before frost/storm in their district
- When wheat crosses their set mandi price threshold
- Monthly "how are you doing?" wellness check for elderly users

---

## Appendix A — Environment Variables Reference

```env
# Core AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Sarvam AI (TTS)
SARVAM_API_KEY=

# LLM
OPENAI_API_KEY=          # optional, for GPT-4o-mini/GPT-4o
LLM_PROVIDER=bedrock     # "openai" or "bedrock"
BEDROCK_MODEL_ID=        # e.g. meta.llama3-3-70b-instruct-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# Storage
DYNAMODB_CALLS_TABLE=vaaniseva-calls
DYNAMODB_KNOWLEDGE_TABLE=vaaniseva-knowledge
DYNAMODB_VECTORS_TABLE=vaaniseva-vectors
DYNAMODB_USERS_TABLE=vaaniseva-users          # Phase 2
DYNAMODB_DISTRESS_TABLE=vaaniseva-distress    # Phase 2
S3_DOCUMENTS_BUCKET=vaaniseva-documents

# Real-time APIs (Phase 2)
DATA_GOV_API_KEY=        # for Agmarknet mandi prices
OPENWEATHER_API_KEY=     # for weather

# Alerting (Phase 2)
ALERT_TOPIC_ARN=         # SNS topic for distress/authority alerts

# App
APP_ENV=development
LOG_LEVEL=INFO
```

## Appendix B — What to Tell Judges About Data Safety

1. **No raw phone numbers stored.** All user identification uses SHA-256 hashed phone numbers. The only place a raw number exists is Twilio's call records (which they control and encrypt).

2. **Knowledge is human-verified.** Every piece of healthcare or legal information has been reviewed by a domain professional before it reaches the system. LLMs are used for conversation, not for generating critical facts.

3. **Distress data is never sold.** The mental health flagging system exists solely to trigger charitable outreach. It is explicitly excluded from any analytics or monetization.

4. **The system degrades gracefully.** If the LLM fails, if Sarvam is down, if Bedrock is unavailable — the caller always hears a human-readable fallback and a real helpline number. The system never leaves someone in silence.

---

*Document maintained by VaaniSeva team. Last updated: March 2026.*
*For technical questions: see `/lambdas/call_handler/handler.py` and `/scripts/`.*
*For pitch materials: see `/prd/` directory.*
