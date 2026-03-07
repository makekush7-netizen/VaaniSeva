# VaaniSeva — Somya's Task List
**Assigned by:** Makewaves  
**Scope:** Website only — `website/` folder  
**DO NOT TOUCH:** `lambdas/`, `scripts/`, `build/`, `connect/`, any `.py` files, `vaani-model-config.json`  

---

## Context

VaaniSeva is a voice AI helpline for rural India built for **AI for Bharat Hackathon 2026** (Problem Statement 3 — Voice AI for Rural India). The backend is fully working. Your job is **only** to fix the website and deploy it.

The website is a **React + Vite + Tailwind** app in the `website/` folder. It already points to the live backend API.

---

## PART A — Content & Bug Fixes

### Fix 1 — Wrong phone number in hero CTA button
**File:** `website/src/pages/Home.jsx` (~line 158)  
The "Call Now" button in the hero section has a wrong number. Fix it:

```jsx
// WRONG (current):
href="tel:+12602048966"

// CORRECT:
href="tel:+19788309619"
```

Also verify the button label reads `Call Now — +1 978 830 9619`.

---

### Fix 2 — Misleading headline: "440 million Indians have no access to AI"
**File:** `website/src/pages/Home.jsx` (~line 112–115)  
This stat is not sourceable and sounds fabricated to judges. Replace with honest framing:

```jsx
// REPLACE this:
440 million Indians have no access to AI.
<br />
VaaniSeva changes that — one phone call at a time.

// WITH this:
Hundreds of millions of Indians have no smartphone, no internet, no access to digital services.
<br />
VaaniSeva changes that — one voice call at a time.
```

---

### Fix 3 — Fake user count in CTA section
**File:** `website/src/pages/Home.jsx` (~line 297)  
"Join 10,000+ Indians already using VaaniSeva" is fabricated — this is a hackathon demo. Judges will notice. Replace with honest copy:

```jsx
// REPLACE:
Join 10,000+ Indians already using VaaniSeva.
No signup needed — just call.

// WITH:
Built for the AI for Bharat Hackathon 2026.
No signup needed — just call us now.
```

---

### Fix 4 — Misleading stat in footer
**File:** `website/src/pages/Home.jsx` (~line 348 in footer section)  
"the Voice-First AI for the other 90% of India" is misleading and vague. Replace:

```jsx
// REPLACE:
VaaniSeva is the Voice-First AI for the other 90% of India.

// WITH:
VaaniSeva is a Voice-First AI helpline built to serve rural and underserved India — accessible from any basic phone, in any language.
```

---

### Fix 5 — Remove voice picker from "Call Me Back" form (BOTH places)
**File:** `website/src/pages/TryPage.jsx`  
The voice selector in the `CallMeBack` component is shown in **two places** — the sticky homepage popup AND the TryPage callback tab. The backend does not use this voice preference — the call is routed by the backend automatically. Showing a fake preference confuses users and judges.

**Step 1:** Delete the `callbackVoices` array at the top of `CallMeBack`:
```jsx
// DELETE this entire block:
const callbackVoices = [
  { code: 'arya',   label: 'Arya',   icon: '👩', hint: 'Female · Hindi' },
  { code: 'vidya',  label: 'Vidya',  icon: '👩', hint: 'Female · EN' },
  { code: 'hitesh', label: 'Hitesh', icon: '👨', hint: 'Male · Hindi' },
]
```

**Step 2:** Delete the `voice` state since it's no longer needed:
```jsx
// DELETE:
const [voice, setVoice] = useState('arya')
```

**Step 3:** Remove `voice` from the fetch body in `handleSubmit`:
```jsx
// CHANGE:
body: JSON.stringify({ phone_number: fullNumber, voice }),

// TO:
body: JSON.stringify({ phone_number: fullNumber }),
```

**Step 4:** Delete the entire `{/* Voice Picker */}` JSX block (~lines 113–133):
```jsx
// DELETE this block:
{/* Voice Picker */}
<div>
  <label className="block text-sm font-medium text-content-primary mb-1.5">
    Preferred Voice <span ...>— आवाज़ चुनें</span>
  </label>
  <div className="flex gap-2">
    {callbackVoices.map(v => (
      ...
    ))}
  </div>
</div>
```

The form should now only show: phone number input → Call Me Now button → disclaimer.

---

### Fix 6 — Improve disclaimer text for judges
**File:** `website/src/pages/TryPage.jsx` (inside `CallMeBack` component, near the bottom)  
Current text is too casual. Make it clearer for hackathon judges:

```jsx
// REPLACE the disclaimer content with:
<p className="text-xs text-amber-700 leading-relaxed">
  <strong>Why a US number?</strong> VaaniSeva is in the trial phase for AI for Bharat Hackathon 2026.
  We are provisioning an Indian toll-free number — until it is active, calls are placed from our US Twilio
  number (+1 978 830 9619). <strong>The call is completely free on our end.</strong> Standard carrier rates
  may apply on your end for international calls. You can also use the Live Call tab above to talk directly
  from your browser — no phone needed.
</p>
```

---

### Fix 7 — Phone dialer is too tall on smaller screens
**File:** `website/src/pages/TryPage.jsx` (~line 783)  
The tab content container has `py-10` padding which makes the dialer need to scroll on smaller screens.

Find this block:
```jsx
<div className="max-w-4xl mx-auto px-6 md:px-12 py-10">
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-sm ${tab === 'voice' ? 'p-6 md:p-10' : 'p-8 md:p-12'}`}>
```

Change the voice tab padding to be smaller and add overflow:
```jsx
<div className="max-w-4xl mx-auto px-6 md:px-12 py-4 md:py-8">
  <div className={`bg-white rounded-2xl border border-gray-100 shadow-sm overflow-y-auto ${tab === 'voice' ? 'p-4 md:p-8' : 'p-8 md:p-12'}`}>
```

Also in `VoiceChat` component, find the language tabs + voice selector section at the top and add `mb-2` instead of `mb-6` to the voice selector wrapper:
```jsx
// FIND (around VoiceChat, Voice Selector section):
<div className="w-full max-w-sm mb-6">

// CHANGE TO:
<div className="w-full max-w-sm mb-3">
```

---

### Fix 8 — 3D Agent widget is built but not wired to backend services
**File:** `website/src/components/VaaniAgent/VaaniWidget.jsx`

The 3D model, animations, lip sync, and speech recognition are **all working**. The widget just calls the **wrong API endpoints** and reads the **wrong response fields**. Do NOT replace the 3D agent — just fix the 3 wiring issues below.

**Background:** The backend has a `/chat` endpoint that returns `{ answer, audio_url }`. The `audio_url` is a pre-generated WAV file on S3 (already synthesized by Sarvam AI). The widget doesn't need a separate TTS call — it just needs to play that URL.

---

**Step 1 — Add a `sessionId` ref at the top of the component**

Find the existing `const recognitionRef = useRef(null)` line and add the session ref right after it:

```jsx
const recognitionRef = useRef(null)
const sessionIdRef = useRef(crypto.randomUUID())   // ← ADD THIS LINE
```

---

**Step 2 — Fix `handleSend()` to call the correct endpoint and read the correct field**

Find the `handleSend` function. Inside the `try` block, find the `fetch` call:

```jsx
// CURRENT (wrong — /web/chat doesn't exist):
const res = await fetch(`${base}/web/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: userMsg })
})
const data = await res.json()

let finalText = data.text || data.message || 'Sorry, something went wrong.'
```

Replace those lines with:
```jsx
// FIXED — correct endpoint, correct fields:
const res = await fetch(`${base}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: userMsg, language: 'hi', session_id: sessionIdRef.current })
})
const data = await res.json()

let finalText = data.answer || 'Sorry, something went wrong.'
```

Also, near the end of `handleSend`'s try block, find where `speakResponse(cleanTTS, finalText)` is called. Change it to pass `data.audio_url` as well:

```jsx
// CURRENT:
if (cleanTTS.length > 0) {
  speakResponse(cleanTTS, finalText)
}

// CHANGE TO:
if (cleanTTS.length > 0) {
  speakResponse(cleanTTS, finalText, data.audio_url)
}
```

---

**Step 3 — Fix `speakResponse()` to use the pre-generated audio_url instead of calling /web/tts**

Find the `speakResponse` function. Its current signature is:
```jsx
const speakResponse = async (text, displayText) => {
```

Change it to:
```jsx
const speakResponse = async (text, displayText, audioUrl) => {
```

Then find the fetch call inside it:
```jsx
// CURRENT (wrong — /web/tts doesn't exist):
const res = await fetch(`${base}/web/tts`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text, lang: 'hi' })
})
```

Replace it with — just fetch the audio URL that `/chat` already returned:
```jsx
// FIXED — fetch the pre-generated audio from S3:
if (!audioUrl) throw new Error('No audio URL')
const res = await fetch(audioUrl)
```

That's it. The rest of the `speakResponse` function (AudioContext, analyser, lip sync, word-by-word subtitles) stays exactly the same — it already handles `res.arrayBuffer()` and does all the animation magic.

---

**What this achieves:**
- User types/speaks → goes to real backend LLM (Amazon Bedrock Nova)
- Backend returns `answer` text + `audio_url` (Sarvam AI WAV on S3)
- Widget fetches WAV from S3 URL → plays through AudioContext
- AudioContext analyser drives real-time mouth-open morph on the 3D avatar
- Word-by-word subtitles appear on the 3D view
- Conversation history is tracked per session via `session_id`

---

### Fix 9 — Vidya label says "Female · EN" (should say "Female · Hindi")
**File:** `website/src/pages/TryPage.jsx` (in VoiceChat's `voices` array, ~line 267)  
```jsx
// FIND:
{ code: 'vidya',  label: 'Vidya',  icon: '👩', hint: 'Female · EN' },

// CHANGE TO:
{ code: 'vidya',  label: 'Vidya',  icon: '👩', hint: 'Female · Health' },
```

---

## PART B — Deployment

The website is a standard Vite React app. Deploy it to **Vercel** — it already has `vercel.json` configured.

### Step-by-Step: Deploy to Vercel

**Prerequisites:** Node.js 18+, npm

#### Option 1 — Vercel Dashboard (easiest for first-time)

1. Go to [vercel.com](https://vercel.com) → Sign up / Log in with GitHub
2. Click **Add New Project**
3. Import the `VaaniSeva` GitHub repo (ask Makewaves to push latest to GitHub if not already there)
4. In the **Configure Project** screen:
   - **Framework Preset:** Vite
   - **Root Directory:** `website` ← **IMPORTANT: set this to `website`, not root**
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Under **Environment Variables**, add:
   ```
   VITE_API_BASE_URL = https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod
   ```
6. Click **Deploy**. Vercel auto-builds and gives you a live URL like `vaaniseva.vercel.app`.

#### Option 2 — Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to the website folder
cd website

# Install dependencies
npm install

# Build locally to check it works first
npm run build

# Deploy to Vercel
vercel

# Follow the prompts:
# - Set root directory to: . (current, since you're already inside website/)
# - Framework: Vite (auto-detected)
# - When asked for env vars, add VITE_API_BASE_URL
```

### Custom Domain (optional)
If you have a domain, add it in Vercel Dashboard → Project → Settings → Domains.

### After Deploying — Test These:
- [ ] Homepage loads, hero video plays
- [ ] "Call Now — +1 978 830 9619" button has correct href
- [ ] Call Me Back popup: only phone number, no voice picker
- [ ] TryPage → Live Call: Twilio dialer loads, you can press call (needs microphone permission)
- [ ] TryPage → Call Me Back: no voice picker, improved disclaimer text
- [ ] Vaani widget (bottom right): opens, chat tab works, 3D tab shows avatar fallback not blank

### Important Environment Note
The website uses `VITE_API_BASE_URL` as the API endpoint. If this env var is missing in Vercel, the site falls back to `http://localhost:8000` which breaks everything in production. **Make sure the env var is set before deploying.**

---

## PART C — Things to Leave Alone

| What | Why |
|------|-----|
| `lambdas/` directory | Live production backend — any change here breaks the phone system |
| `scripts/` directory | Deployment scripts only Makewaves should run |
| `build/` directory | Auto-generated Lambda build artifact |
| `vaani-model-config.json` | Backend config |
| `connect/` directory | Amazon Connect flow |
| Any `.py` files | Python backend |
| `lambdas/call_handler/handler.py` | **Especially DO NOT touch this — it's the main AI brain** |

---

## Summary of Changes

| # | File | Change |
|---|------|--------|
| 1 | `Home.jsx` | Fix hero CTA phone number (+12602048966 → +19788309619) |
| 2 | `Home.jsx` | Rewrite "440 million" headline |
| 3 | `Home.jsx` | Replace "10,000+ Indians" fake stat |
| 4 | `Home.jsx` | Rewrite footer tagline |
| 5 | `TryPage.jsx` | Remove voice picker from CallMeBack component |
| 6 | `TryPage.jsx` | Improve disclaimer text |
| 7 | `TryPage.jsx` | Reduce dialer height/padding |
| 8 | `VaaniWidget.jsx` | Replace broken 3D canvas with static avatar |
| 9 | `TryPage.jsx` | Fix Vidya voice label |
| 10 | `website/` | Deploy to Vercel with correct env var |

---

*Generated by GitHub Copilot for VaaniSeva — Team Prayas, AI for Bharat Hackathon 2026*
