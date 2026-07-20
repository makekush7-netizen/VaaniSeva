# VaaniSeva — Complete Dev Handoff Context

> **Purpose**: This file is a complete technical handoff for continuing development in a new chat session. Any AI agent reading this should be able to understand the full project architecture, codebase structure, RAG pipeline, multi-agent system, 3D avatar system, deployment process, and current status.
>
> **Last updated**: June 24, 2026

---

## 1. What Is VaaniSeva

VaaniSeva (वाणीसेवा, "Voice Service") is a **voice-first AI platform** designed to bridge India's digital divide. It lets users call a phone number, speak in their native language (Hindi/Marathi/Tamil/English), and get an AI-powered spoken answer about government schemes, healthcare, agriculture, and more.

The project has **two completely separate AI systems**:

1. **Phone Calling Agent** — Twilio-based telephony system with RAG pipeline, multi-agent personalities (Arya/Hitesh/Vidya), live mandi price API, and web search
2. **Web Agent (Vaani)** — Dedicated AI for the website's 3D avatar widget with emotion/animation system, separate Lambda, separate API Gateway

**Hackathon project** — AI for Bharat Hackathon 2026, Problem Statement 3.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite 5 + Tailwind CSS 3 + React Router 6 + Framer Motion |
| **3D Avatar** | Three.js + @react-three/fiber + @react-three/drei (GLB model) |
| **Browser Voice** | @twilio/voice-sdk v2.18 (WebRTC) |
| **Phone Backend** | AWS Lambda (Python 3.11) — `vaaniseva-call-handler` |
| **Web Agent Backend** | AWS Lambda (Python 3.11) — `vaaniseva-web-agent` (SEPARATE) |
| **API Gateway** | REST — `https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod` (call handler) |
| **Web Agent API** | REST — separate API Gateway for `/vaani/chat` and `/vaani/stt` |
| **Database** | AWS DynamoDB (5 tables) |
| **Storage** | AWS S3 bucket `vaaniseva-documents` |
| **Primary LLM** | Amazon Bedrock Nova Lite (call handler) / Amazon Nova Lite (web agent) |
| **Fallback LLM** | OpenAI GPT-4o-mini (if `OPENAI_API_KEY` set and `LLM_PROVIDER=openai`) |
| **STT (Phone)** | Twilio native speech recognition (Gather) + Sarvam Saaras v3 (for recordings) |
| **STT (Web)** | Sarvam Saarika v2 (via MediaRecorder) + browser Web Speech API fallback |
| **TTS** | Sarvam AI Bulbul v2 (primary) → Amazon Polly (fallback) |
| **TTS (Web Agent)** | Sarvam AI Bulbul v2 (returns base64 WAV directly, no S3) |
| **Alternative TTS** | Cartesia Sonic-3 (configurable via `TTS_PROVIDER=cartesia`) |
| **Embeddings** | AWS Bedrock Titan Embed v2 |
| **Telephony** | Twilio Voice API |
| **Auth** | Custom JWT (PBKDF2 passwords, PyJWT, DynamoDB users table) |
| **Web Search** | Tavily API → Serper API → DuckDuckGo HTML scrape → DDG Instant API (cascading fallback) |
| **Live Data** | data.gov.in Agmarknet API (mandi prices) |
| **Deployment** | Custom Python deploy script (`scripts/deploy.py`) |
| **Frontend Hosting** | Vercel (config ready, not yet deployed) |

---

## 3. Architecture Overview

### 3.1 Phone Calling System (Main Pipeline)

```
Caller dials +1 978 830 9619
        │
        ▼
Twilio Voice API
        │
        ▼
POST /voice/incoming → Lambda handler.py
        │
        ├── First-time caller: DTMF language menu (1=hi, 2=mr, 3=ta, 4=en)
        │   └── Or returning caller: phone_profiles lookup → skip menu
        │
        ▼
POST /voice/language-detect → Auto-detect language from speech
        │
        ▼
POST /voice/gather → Main conversation loop
        │
        ├── Goodbye detection → hangup
        ├── Language switch detection → switch mid-call
        ├── Agent switch detection → [SWITCH:arya|hitesh|vidya]
        ├── Fast path (no data needed): LLM → TTS → play → gather again
        └── Data path ([FETCH_DATA] or [WEB_SEARCH]):
            ├── Play "thinking" ack
            ├── Async: RAG retrieval + Mandi API + Web Search (parallel)
            ├── Phase 2 LLM with context → TTS
            └── Poll endpoint → play answer → gather again
```

### 3.2 Web Agent System (Vaani Avatar — COMPLETELY SEPARATE)

```
Browser mic / text input
        │
        ▼
VaaniWidget.jsx (React component)
        │
        ├── POST /vaani/chat → Web Agent Lambda (handler.py in lambdas/web_agent/)
        │   ├── Bedrock Nova Lite (system prompt: Vaani persona)
        │   ├── Parse [EMOTION:xxx] and [NAV:/path] tags
        │   ├── Sarvam TTS → base64 WAV (no S3)
        │   └── Return { answer, audio_base64, emotion, nav_target }
        │
        └── POST /vaani/stt → Sarvam Saarika v2 STT
            └── Return { transcript, language }
```

### 3.3 WebSocket System (Built but NOT deployed)

```
Browser mic → WebSocket → Lambda (lambdas/websocket_handler/)
    ├── OpenAI Whisper STT
    ├── RAG + GPT-4o-mini
    └── Sarvam TTS → S3 presigned URL → Browser
```

---

## 4. Lambda Functions

### 4.1 `lambdas/call_handler/handler.py` (3102 lines) — MAIN BACKEND

**The single largest and most important file.** Handles ALL phone call logic, REST API routes, RAG pipeline, TTS, auth, admin, and more.

**Routes handled:**
- `/voice/incoming` — Twilio webhook for new calls
- `/voice/language` — DTMF language selection
- `/voice/language-detect` — Auto language detection from speech
- `/voice/gather` — Main conversation loop (speech → RAG → TTS)
- `/voice/stt` — Recording-based STT (Sarvam Saaras v3)
- `/voice/poll` — Poll for async RAG results
- `/voice/token` — Twilio Access Token for browser WebRTC
- `/voice/voice-select` — Voice/agent selection menu
- `/voice/transcribe-token` — STS credentials for browser-side Transcribe
- `/voice/transcribe` — Server-side Amazon Transcribe
- `/call/initiate` — Outbound "Call Me Back"
- `/chat` — Text chat REST endpoint
- `/auth/register` — User registration
- `/auth/login` — User login (returns JWT)
- `/profile` — GET/POST user profile
- `/profile/history` — Call history
- `/admin/rag` — CRUD for knowledge entries + AI review + verify

**Key classes/structures:**
- `LANG_CONFIG` — Language configs for hi, mr, ta, en
- `AGENT_REGISTRY` — 3 agents: Arya (schemes/legal), Hitesh (agriculture), Vidya (health)
- `VOICE_OPTIONS` — 3 voices: arya (female), vidya (female), hitesh (male)
- `DIGIT_TO_LANG` / `DIGIT_TO_VOICE` — DTMF mappings

**Key functions:**
- `build_system_prompt()` — Dynamic system prompt per agent + language + user profile
- `detect_agent_from_intent()` — Routes to right agent based on keywords
- `sarvam_tts()` — Sarvam Bulbul v2 TTS → S3 → presigned URL
- `_cartesia_tts()` — Cartesia Sonic-3 TTS (alternative)
- `_sarvam_stt()` — Sarvam Saaras v3 STT
- `_cached_tts()` — In-memory TTS cache for static phrases
- `tts_say()` — Add TTS audio to TwiML (Sarvam → Polly fallback)
- `rag_pipeline()` — Main RAG: embedding → retrieve → LLM
- `get_embedding()` — Bedrock Titan Embed v2
- `retrieve_context()` — Cosine similarity scan of vectors table
- `ask_llm()` — Bedrock (primary) → OpenAI (fallback)
- `_fetch_data_gov()` — Live mandi prices from data.gov.in
- `_fetch_web_search()` — Tavily → Serper → DDG HTML → DDG API (cascading)
- `should_use_rag()` — Decides if RAG is needed for the utterance
- `_hash_phone()` — SHA-256 phone hashing for privacy
- `detect_language_from_speech()` — Character-based language detection
- `summarize_and_store_call()` — Cross-call memory via Bedrock summarization
- `_tts_chunks_parallel()` — Parallel TTS for long responses
- `_split_for_tts()` — Sentence-boundary chunking for TTS
- `_build_profile_context()` — User profile injection into LLM prompt
- `_lookup_user_by_phone()` — Registered user lookup by phone number
- `_get_phone_profile()` — Phone profiles table lookup
- `handle_admin_routes()` — Full CRUD for knowledge entries
- `_handle_admin_ai_review()` — AI fact-checking via Bedrock
- `_handle_admin_verify_rag()` — Human verification marking

### 4.2 `lambdas/call_handler/connect_handler.py` (195 lines)

Amazon Connect integration handler. Invoked by Contact Flow. Imports pure functions from handler.py. Supports `init`, `set_language`, and `query` actions.

### 4.3 `lambdas/call_initiator/handler.py` (162 lines)

Standalone outbound call Lambda. Validates E.164 format, rate-limits (2 calls/hour), initiates Twilio outbound call. **Logic merged into main handler.py** — this file is legacy.

### 4.4 `lambdas/web_agent/handler.py` (390 lines) — VAANI WEB AGENT

**COMPLETELY SEPARATE from the phone calling agent.** Dedicated AI for the website's 3D avatar.

**Routes:**
- `POST /vaani/chat` — { message, history, language } → { answer, audio_base64, emotion, nav_target }
- `POST /vaani/stt` — { audio_base64, language } → { transcript, language }
- `GET /vaani/health` — Health check

**Key features:**
- Uses `VAANI_SYSTEM_PROMPT` — Vaani persona (warm, female, web assistant)
- Returns `[EMOTION:xxx]` tags for avatar animation
- Returns `[NAV:/path]` tags for page navigation
- Sarvam TTS returns base64 WAV directly (no S3 needed)
- Sarvam STT via Saarika v2
- Bedrock Nova Lite via Converse API

### 4.5 `lambdas/websocket_handler/handler.py` (455 lines)

WebSocket-based voice pipeline. **Built but NOT deployed.** Uses OpenAI Whisper for STT, imports RAG from main handler, Sarvam TTS. Stores connections in `vaaniseva-ws-connections` DynamoDB table.

---

## 5. Multi-Agent System

The phone system has **3 distinct AI agents** with different personalities, domains, and voices:

| Agent | Name (Hindi) | Gender | Domain | Sarvam Speaker | Personality |
|-------|-------------|--------|--------|---------------|-------------|
| **Arya** | आर्या | Female | Schemes, legal rights, government benefits, general | arya | Warm, friendly, default agent |
| **Hitesh** | हितेश | Male | Agriculture, mandi prices, crop insurance, farming | abhilash (mapped) | Direct, practical, farming background |
| **Vidya** | विद्या | Female | Health, mental wellness, medical schemes, ASHA | vidya | Gentle, deeply caring, health worker |

**Agent switching:**
- User says "mujhe hitesh se baat karao" → `[SWITCH:hitesh]` tag
- LLM can autonomously switch via `[SWITCH:agent_name]` tag
- Intent detection routes to right agent based on keywords (agriculture → Hitesh, health → Vidya)

**The web agent (Vaani) is a completely separate persona** — NOT one of these three.

---

## 6. RAG Pipeline (Verified Knowledge Retrieval)

### 6.1 Flow

```
User query
    │
    ▼
should_use_rag() → Skip for greetings, short utterances, live data queries
    │
    ▼ (if RAG needed)
get_embedding(query) → Bedrock Titan Embed v2
    │
    ▼
retrieve_context(embedding, language) → Cosine similarity scan of vaaniseva-vectors table
    │   Returns top-3 chunks, language-prioritized (native lang → Hindi → English)
    │
    ▼
_fetch_data_gov(query) → Live mandi prices from data.gov.in (if API key set)
    │
    ▼
_fetch_web_search(query) → Web search (if [WEB_SEARCH] tag emitted)
    │
    ▼
ask_llm(query, context, language, history, profile_context) → Bedrock → OpenAI fallback
    │
    ▼
TTS → Play to caller
```

### 6.2 Database Tables

| Table | Partition Key | Purpose |
|-------|--------------|---------|
| `vaaniseva-calls` | `call_id` (String) | Call records, conversation history, rate limiting |
| `vaaniseva-knowledge` | `scheme_id` (String) + `section_id` (String) | Knowledge entries with multilingual text |
| `vaaniseva-vectors` | `embedding_id` (String) | Embeddings for cosine similarity search |
| `vaaniseva-users` | `user_id` (String) | User accounts (NOT created yet) |
| `vaaniseva-phone-profiles` | `phone_hash` (String) | Cross-call memory, language preferences |
| `vaaniseva-ws-connections` | `connection_id` (String) | WebSocket connections (not deployed) |

### 6.3 Knowledge Entry Schema

```python
{
  "scheme_id": "pm-kisan",
  "section_id": "overview",  # or "faqs"
  "category": "agriculture",  # health, finance, housing, women, education
  "verified": True,
  "verified_by": "reviewer_id",
  "verified_at": 1741200000,
  "ai_review_status": "PASS",  # PASS / FLAG / FAIL
  "ai_review_notes": "",
  "source_url": "https://pmkisan.gov.in",
  "text_hi": "...",  # Hindi Devanagari
  "text_mr": "...",  # Marathi
  "text_ta": "...",  # Tamil
  "text_en": "...",  # English
  "helpline_numbers": ["155261"],
  "eligibility_summary": "...",
  "documents_required": ["Aadhaar", "Land record"],
  "embedding": [...]  # In vectors table
}
```

### 6.4 Seeded Data

The `scripts/seed_knowledge.py` script seeds **30+ government schemes** with full multilingual content (hi, mr, ta, en) including:
- PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas Yojana, Sukanya Samriddhi
- PM Mudra, PM Fasal Bima, Atal Pension, PM SVANidhi, Beti Bachao
- Janani Suraksha, PM Garib Kalyan Anna, Jan Dhan, PM Ujjwala
- National Scholarship, Soil Health Card, PM POSHAN, Mahila Samman
- PM Kaushal Vikas, PM Suraksha Bima, PM Jeevan Jyoti, Stand Up India
- PM Matru Vandana, National Family Benefit, Samagra Shiksha, RBSK
- Saubhagya, Swachh Bharat, PM Shram Yogi Mandhan, PM Vishwakarma
- JSSK, PM Krishi Sinchai

Each scheme has FAQ sections with detailed Q&A in all 4 languages.

### 6.5 Critical Information Lock

For helpline numbers, the LLM is **NOT allowed to generate these from scratch**. Verified numbers are injected directly into the TTS response after the LLM answer:

```python
if structured_data.get("helpline_numbers"):
    verified_suffix = f"हेल्पलाइन नंबर है: {structured_data['helpline_numbers'][0]}"
    llm_answer = llm_answer + " " + verified_suffix
```

---

## 7. Web Frontend

### 7.1 Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Home.jsx | Landing page with scheme cards, hero video |
| `/try` | TryPage.jsx | Live Call (WebRTC) + Call Me Back tabs |
| `/login` | Login.jsx | Email/password login |
| `/register` | Register.jsx | User registration |
| `/profile` | Profile.jsx | Edit profile + call history |
| `/pricing` | Pricing.jsx | Free/Pro/Business tiers |
| `/dev` | DevConsolePage.jsx | Developer tools |
| `/admin` | AdminPage.jsx | RAG knowledge base admin |
| `/sim` | PhoneSimulatorPage.jsx | Phone simulator |

### 7.2 Vaani Widget (3D Avatar)

**Location:** `website/src/components/VaaniAgent/`

**Files:**
- `VaaniWidget.jsx` (449 lines) — Main chat widget with 3D avatar, text/voice input, emotion system
- `AvatarModel.jsx` (320 lines) — Three.js GLB avatar with idle animation, eye tracking, blinking, lip sync, emotional morphs
- `styles.css` — Widget styling

**Key features:**
- Floating button with mini 3D avatar preview
- Two modes: 3D Agent (avatar) and Chat (text-only)
- Voice input via Sarvam STT (MediaRecorder) → browser STT fallback
- Lip sync via audio amplitude analysis (AnalyserNode)
- Emotion-driven animations: happy, laugh, shock, sad, thankful, thinking
- Eye tracking follows camera position
- Breathing animation, random blinking, head sway
- Chat history stored in localStorage
- Quick action chips for common questions
- Navigation actions via `[NAV:/path]` tags

**Avatar model:** `/models/vaani.glb` (Ready Player Me / Mixamo compatible)

**Event system (CustomEvents on window):**
- `aura:setMorph` — { name, value } for morph target control
- `aura:setEye` — { yaw, pitch } for eye direction
- `aura:setEmotion` — emotion name string
- `aura:talking` — boolean for talk animation
- `aura:setAnimation` — clip name string

### 7.3 Auth System

**Context:** `website/src/context/AuthContext.jsx`
- JWT stored in localStorage
- Login/register/profile API calls
- Auth-aware Navbar

---

## 8. Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.py` | Full AWS deployment: packages Lambda, creates/updates API Gateway, updates Twilio webhook, deploys web agent Lambda |
| `scripts/seed_knowledge.py` | Seeds DynamoDB with 30+ government schemes in 4 languages (hi, mr, ta, en) with embeddings |
| `scripts/local_server.py` | Flask dev server on port 8000 — proxies ALL Lambda routes for local testing |
| `scripts/vaani_web_server.py` | Flask dev server on port 8001 — proxies web agent routes |
| `scripts/seed_task1c.py` | Additional seed data |
| `scripts/add_translations.py` | Add translations to knowledge base |
| `scripts/add_faq_translations.py` | Add FAQ translations |
| `scripts/check_deployment.py` | Check deployment status |
| `scripts/check_syntax.py` | Python syntax checker |
| `scripts/dashboard.py` | Dashboard utility |
| `scripts/generate_welcome_audio.py` | Generate welcome audio files |
| `scripts/test_aws_access.py` | Test AWS credentials |
| `scripts/test_bedrock.py` | Test Bedrock model access |
| `scripts/test_call.py` | Test Twilio call flow |
| `scripts/test_cartesia.py` | Test Cartesia TTS |
| `scripts/test_elevenlabs.py` | Test ElevenLabs TTS |
| `scripts/test_elevenlabs2.py` | Test ElevenLabs TTS (alt) |
| `scripts/test_voices.py` | Test available voices |

---

## 9. Environment Variables

### 9.1 Root `.env` (Backend)

```env
# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=+19788309619
TWILIO_API_KEY_SID=        # For browser WebRTC
TWILIO_API_KEY_SECRET=     # For browser WebRTC
TWILIO_TWIML_APP_SID=     # For browser WebRTC

# API
API_BASE_URL=https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod

# TTS
SARVAM_API_KEY=
CARTESIA_API_KEY=          # Optional alternative TTS
TTS_PROVIDER=sarvam        # "sarvam" or "cartesia"

# LLM
OPENAI_API_KEY=            # Optional, for GPT-4o-mini fallback
LLM_PROVIDER=bedrock       # "openai" or "bedrock"
BEDROCK_MODEL_ID=amazon.nova-lite-v1:0
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0

# DynamoDB
DYNAMODB_CALLS_TABLE=vaaniseva-calls
DYNAMODB_KNOWLEDGE_TABLE=vaaniseva-knowledge
DYNAMODB_VECTORS_TABLE=vaaniseva-vectors
DYNAMODB_USERS_TABLE=vaaniseva-users
DYNAMODB_PHONE_PROFILES_TABLE=vaaniseva-phone-profiles
DYNAMODB_WS_CONNECTIONS_TABLE=vaaniseva-ws-connections

# S3
S3_DOCUMENTS_BUCKET=vaaniseva-documents

# Auth
JWT_SECRET=
PHONE_HASH_SALT=vaaniseva-salt-2026

# Web Search
TAVILY_API_KEY=            # Best, sign up at tavily.com
SERPER_API_KEY=            # Fallback, 2500 req/month free

# Live Data
DATA_GOV_API_KEY=          # For Agmarknet mandi prices

# App
APP_ENV=development
LOG_LEVEL=INFO
```

### 9.2 `website/.env` (Frontend)

```env
VITE_API_BASE_URL=https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod
VITE_API_BASE=https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod
VITE_TWILIO_PHONE=+19788309619
VITE_VAANI_API=https://your-web-agent-api-id.execute-api.us-east-1.amazonaws.com/prod
```

---

## 10. Deployment

### 10.1 Full AWS Deploy

```bash
python scripts/deploy.py
```

This does:
1. Packages `lambdas/call_handler/handler.py` + `connect_handler.py` + dependencies (twilio, requests, pyjwt, aiohttp) into a zip
2. Uploads to S3 `vaaniseva-documents/deployments/call_handler.zip`
3. Creates/updates `vaaniseva-call-handler` Lambda (Python 3.11, 1024MB, 30s timeout)
4. Creates/updates API Gateway with ALL routes (voice, call, auth, profile, admin, chat)
5. Updates Twilio phone number webhook to point to API Gateway
6. Adds Amazon Connect invoke permission
7. Packages and deploys `vaaniseva-web-agent` Lambda (Python 3.11, 512MB, 30s timeout)
8. Creates/updates Web Agent API Gateway with `/vaani/chat` and `/vaani/stt` routes

### 10.2 Web Agent Only Deploy

```bash
python scripts/deploy.py --web-agent
```

### 10.3 Frontend Deploy (Vercel)

```bash
cd website
npx vercel --prod
```

Set env vars in Vercel dashboard.

### 10.4 Seed Knowledge Base

```bash
python scripts/seed_knowledge.py
```

Run ONCE after DynamoDB tables are created.

---

## 11. Current Status

### ✅ Working
- **Phone calls** — dial +1 978 830 9619, select language, speak, get AI answer
- **Multi-language** — Hindi, Marathi, Tamil, English (4 languages)
- **Multi-agent** — Arya (default), Hitesh (agriculture), Vidya (health) with mid-call switching
- **Browser Live Call** — TryPage → Twilio WebRTC via @twilio/voice-sdk
- **Call Me Back** — Enter phone number, Twilio places outbound call
- **Text fallback** — Type questions, get answers with TTS audio
- **RAG pipeline** — Embeddings → cosine similarity → LLM → TTS
- **Live mandi prices** — data.gov.in Agmarknet API integration
- **Web search** — Tavily → Serper → DuckDuckGo cascading fallback
- **Cross-call memory** — Phone profiles table stores language, agent preference, last topic
- **Returning caller detection** — Skip language menu for known callers
- **Goodbye detection** — Multi-language goodbye phrases trigger hangup
- **Language auto-detection** — Character-based (Devanagari/Tamil/ASCII)
- **Mid-call language switch** — "hindi mein baat karo" → switches conversation language
- **Mid-call voice switch** — "change voice" → voice selection menu
- **TTS caching** — In-memory cache for static phrases on warm Lambda
- **Parallel TTS** — Long responses chunked and synthesized in parallel
- **Local dev server** — `scripts/local_server.py` (port 8000) + `scripts/vaani_web_server.py` (port 8001)
- **Vaani 3D Avatar** — Website widget with full animation, lip sync, emotion system
- **Admin RAG CRUD** — Full create/read/update/delete for knowledge entries
- **AI Review** — Bedrock-based fact-checking for knowledge entries
- **Human Verification** — Mark entries as verified by human reviewer
- **data.gov.in** — Live scheme data augmentation
- **OG meta tags** — Twitter/OG tags in index.html
- **Vercel config** — `website/vercel.json` ready

### ⚠️ Built but NOT Deployed / Needs Setup
- **`vaaniseva-users` DynamoDB table** — NOT created yet (needs manual creation in AWS console)
- **`vaaniseva-phone-profiles` DynamoDB table** — NOT created yet
- **User auth routes** — `/auth/*`, `/profile*` exist in code but API Gateway routes may not be fully deployed
- **Web Agent API Gateway** — May need deployment (`python scripts/deploy.py --web-agent`)
- **Vercel deployment** — Config ready, not deployed yet
- **Full AWS redeploy** — Run `python scripts/deploy.py` to push all changes

### ❌ Not Done / Future
- **WebSocket handler** — Built but not deployed (not needed for current scope)
- **Bhashini integration** — Deferred (API not available under hackathon free tier)
- **Emotion scoring / mental health system** — Designed in PRD, not implemented in code
- **User tier system** — Designed in PRD (free/registered/pro/institutional), not implemented
- **SMS summaries** — Planned but not built
- **WhatsApp integration** — Future roadmap
- **Proactive outbound calls** — Future roadmap
- **UMANG API integration** — Future roadmap

---

## 12. Key Implementation Details

### 12.1 Browser Voice Call Flow
1. User clicks phone button on `/try` page
2. Frontend fetches `GET /voice/token?language=hi`
3. Backend issues Twilio Access Token (API Key + TwiML App)
4. `@twilio/voice-sdk` `Device.connect({ params: { lang: 'hi' } })` creates WebRTC call
5. Twilio calls TwiML App webhook → `POST /voice/incoming?lang=hi`
6. Lambda detects `lang` param → skips DTMF menu → `_browser_call_welcome()`
7. Greets in chosen language → `<Gather>` for speech → `/voice/gather?lang=hi`
8. Speech → RAG → LLM → TTS → plays back

### 12.2 Call Me Back Flow
1. User submits phone number on `/try` → "Call Me Back" tab
2. Frontend POSTs to `/call/initiate` with `{ phone_number: "+91..." }`
3. Backend rate-limits (2 calls/hour), then `twilio_client.calls.create()`
4. Webhook URL is ALWAYS hardcoded to `API_BASE_URL` env var (production API Gateway)
5. Twilio calls user's phone → same voice pipeline

### 12.3 Auth System
- Passwords hashed with PBKDF2-HMAC-SHA256 (100k iterations)
- Tokens: PyJWT HS256, 7-day expiry, stored in localStorage
- Falls back to HMAC-signed JSON blob if PyJWT not installed
- Profile fields: name, phone, language, occupation, state, district, enrolled_schemes, custom_context
- Profile injected into LLM prompt via `_build_profile_context()`

### 12.4 TTS Pipeline
- **Primary:** Sarvam AI Bulbul v2 → S3 WAV → presigned URL → Twilio `<Play>`
- **Fallback:** Amazon Polly via Twilio `<Say>` (no extra config)
- **Web Agent:** Sarvam AI Bulbul v2 → base64 WAV → browser AudioContext
- **Alternative:** Cartesia Sonic-3 (40ms TTFA, emotion support)
- **Caching:** In-memory dict for static phrases (survives warm Lambda invocations)
- **Chunking:** Long text split at sentence boundaries (। ? ! .), synthesized in parallel

### 12.5 Web Search (Cascading Fallback)
1. **Tavily API** (best, sign up free at tavily.com)
2. **Serper API** (Google Search, 2500 req/month free)
3. **DuckDuckGo HTML scrape** (stdlib HTML parser, no API key)
4. **DuckDuckGo Instant Answer API** (factual fallback)

### 12.6 LLM Prompt Engineering
The system prompt includes:
- Named identity reinforcement (agent refers to itself by name)
- Emotional mirroring cues
- Regional vocabulary seeding
- Conversation arc awareness (phone call, not chat)
- Filler naturalness instructions
- `[FETCH_DATA]` and `[WEB_SEARCH]` tag protocol
- `[SWITCH:agent]` tag protocol
- `[HANGUP]` tag protocol
- Language adherence instructions
- Helpline number injection rules

### 12.7 Privacy
- Phone numbers stored as SHA-256 hashes with salt
- Raw numbers only exist in Twilio's call records
- Twilio recordings deleted after transcription (fire-and-forget)
- Distress data explicitly excluded from analytics/monetization

---

## 13. Repository Structure

```
VaaniSeva/
├── .env                          # Real credentials (gitignored)
├── .env.example                  # Environment variable template
├── .gitignore
├── README.md                     # Project overview
├── HANDOFF.md                    # This file
├── DESIGN.md                     # Design document
├── PPTCONTENT.MD                 # Pitch deck content
├── pptcreation.md                # PPT creation notes
├── TEAM_TASKS.md                 # Team task tracking
├── requirements.txt              # Python dependencies
├── vaani-model-config.json       # Avatar model config (animations, morphs, bones)
├── VaaniIcons_Preview.html       # Icon preview
├── hero.mp4                      # Hero video
│
├── lambdas/
│   ├── call_handler/
│   │   ├── handler.py            ★ MAIN BACKEND (3102 lines) — all routes, RAG, TTS, auth
│   │   └── connect_handler.py    — Amazon Connect event handler
│   ├── call_initiator/
│   │   └── handler.py            — Standalone outbound call (legacy, logic merged)
│   ├── web_agent/
│   │   └── handler.py            ★ VAANI WEB AGENT (390 lines) — separate from phone
│   └── websocket_handler/
│       └── handler.py            — WebSocket pipeline (built, not deployed)
│
├── website/
│   ├── .env.example              — Frontend env vars
│   ├── .env.local                — Local frontend env
│   ├── index.html                — Entry HTML with OG tags
│   ├── package.json              — React + Three.js + Twilio SDK
│   ├── vite.config.js            — Vite config
│   ├── tailwind.config.js        — Tailwind config
│   ├── postcss.config.js         — PostCSS config
│   ├── vercel.json               — Vercel deployment config
│   ├── public/
│   │   ├── favicon.svg
│   │   ├── hero.mp4
│   │   └── models/
│   │       └── vaani.glb         ★ 3D Avatar model
│   ├── dist/                     — Built output
│   └── src/
│       ├── main.jsx              — React entry
│       ├── App.jsx               — Routes, AuthProvider, VaaniWidget
│       ├── index.css             — Tailwind + custom styles
│       ├── context/
│       │   └── AuthContext.jsx   — JWT auth state
│       ├── pages/
│       │   ├── Home.jsx          — Landing page
│       │   ├── TryPage.jsx       — Live Call + Call Me Back
│       │   ├── Login.jsx         — Login form
│       │   ├── Register.jsx      — Registration form
│       │   ├── Profile.jsx       — Profile + call history
│       │   ├── Pricing.jsx       — Pricing tiers
│       │   ├── AdminPage.jsx     — RAG admin CRUD
│       │   ├── DevConsolePage.jsx— Developer tools
│       │   └── PhoneSimulatorPage.jsx — Phone simulator
│       └── components/
│           ├── layout/
│           │   └── Navbar.jsx    — Auth-aware navigation
│           ├── icons/
│           │   └── VaaniIcons.jsx— Custom icons
│           └── VaaniAgent/
│               ├── VaaniWidget.jsx  ★ Main chat widget (449 lines)
│               ├── AvatarModel.jsx  ★ 3D avatar with animation (320 lines)
│               └── styles.css       — Widget styling
│
├── scripts/
│   ├── deploy.py                 ★ Full AWS deployment script (591 lines)
│   ├── seed_knowledge.py         ★ Seeds 30+ schemes in 4 languages (4228 lines)
│   ├── local_server.py           — Flask dev server (port 8000)
│   ├── vaani_web_server.py       — Flask dev server (port 8001)
│   ├── seed_task1c.py            — Additional seed data
│   ├── add_translations.py       — Translation utilities
│   ├── add_faq_translations.py   — FAQ translation utilities
│   ├── check_deployment.py       — Deployment checker
│   ├── check_syntax.py           — Python syntax checker
│   ├── dashboard.py              — Dashboard utility
│   ├── generate_welcome_audio.py — Welcome audio generator
│   ├── test_aws_access.py        — AWS credential tester
│   ├── test_bedrock.py           — Bedrock model tester
│   ├── test_call.py              — Call flow tester
│   ├── test_cartesia.py          — Cartesia TTS tester
│   ├── test_elevenlabs.py        — ElevenLabs tester
│   ├── test_elevenlabs2.py       — ElevenLabs alt tester
│   └── test_voices.py            — Voice tester
│
├── connect/
│   └── contact-flow-vaaniseva.json — Amazon Connect contact flow
│
├── prd/
│   ├── VAANISEVA_PRD.md          ★ Product Requirements Document (655 lines)
│   └── contex.md                 — Additional context
│
├── large models/
│   ├── model_female.glb          — Female avatar model
│   ├── hero.mp4                  — Hero video
│   └── README.md                 — Model documentation
│
└── build/
    └── lambda_package/           — Lambda build artifacts (gitignored)
```

---

## 14. Quick Start for New Developers

### Local Development

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start backend (port 8000)
python scripts/local_server.py

# 4. In another terminal, start web agent server (port 8001)
python scripts/vaani_web_server.py

# 5. Install frontend dependencies
cd website
npm install

# 6. Start frontend (port 3001)
npm run dev
```

### First-Time AWS Setup

```bash
# 1. Create DynamoDB tables in AWS console:
#    - vaaniseva-calls (PK: call_id String)
#    - vaaniseva-knowledge (PK: scheme_id String, SK: section_id String)
#    - vaaniseva-vectors (PK: embedding_id String)
#    - vaaniseva-users (PK: user_id String) — NOT created yet
#    - vaaniseva-phone-profiles (PK: phone_hash String) — NOT created yet

# 2. Create IAM role: vaaniseva-lambda-role with:
#    - AWSLambdaBasicExecutionRole
#    - AmazonDynamoDBFullAccess
#    - AmazonBedrockFullAccess
#    - AmazonPollyFullAccess
#    - AmazonS3FullAccess

# 3. Deploy to AWS
python scripts/deploy.py

# 4. Seed knowledge base
python scripts/seed_knowledge.py
```

---

## 15. Key Files to Read for Deep Understanding

| File | Lines | Why Read |
|------|-------|----------|
| `lambdas/call_handler/handler.py` | 3102 | **The entire backend** — all routes, RAG, TTS, auth, admin |
| `lambdas/web_agent/handler.py` | 390 | **Vaani web agent** — separate AI for website avatar |
| `website/src/components/VaaniAgent/VaaniWidget.jsx` | 449 | **Main chat widget** — 3D avatar, voice, emotion system |
| `website/src/components/VaaniAgent/AvatarModel.jsx` | 320 | **3D avatar** — animation, lip sync, eye tracking |
| `prd/VAANISEVA_PRD.md` | 655 | **Product requirements** — full vision, architecture, roadmap |
| `scripts/deploy.py` | 591 | **Deployment** — Lambda packaging, API Gateway, Twilio webhook |
| `scripts/seed_knowledge.py` | 4228 | **Knowledge base** — 30+ schemes in 4 languages |
| `vaani-model-config.json` | 281 | **Avatar config** — animations, morphs, bones, events |

---

## 16. Common Gotchas

1. **Twilio trial account** — Can only call verified numbers. Unverified numbers get an error.
2. **Lambda cold starts** — First call after inactivity may take 2-3 seconds longer.
3. **TTS caching** — In-memory cache resets on cold starts but persists across warm invocations.
4. **Web search API keys** — Tavily is best but needs signup. Serper is free for 2500 req/month.
5. **DynamoDB scans** — `retrieve_context()` does a full table scan. Fine for hackathon scale (<1000 items) but needs proper indexing for production.
6. **API Gateway routes** — The deploy script creates routes, but if you add new routes to handler.py, you need to add them to `create_api_gateway()` in deploy.py too.
7. **Web Agent is SEPARATE** — Do NOT merge web_agent/handler.py with call_handler/handler.py. They have different system prompts, different TTS pipelines, and different purposes.
8. **Phone number hashing** — `PHONE_HASH_SALT` in .env must be consistent across deployments or returning caller detection breaks.
9. **Twilio webhook URL** — Must be a public URL (not localhost). The deploy script sets it to the API Gateway URL.
10. **Vite API URLs** — Frontend uses `VITE_API_BASE_URL` for calling agent and `VITE_VAANI_API` for web agent. These are different URLs.

---

*Document maintained by VaaniSeva team. For questions: makewatch7@gmail.com*
*Last updated: June 24, 2026*