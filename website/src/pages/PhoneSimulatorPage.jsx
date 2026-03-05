/**
 * PhoneSimulatorPage — Simulates the EXACT Twilio phone call flow in the browser.
 *
 * Calls the SAME Lambda endpoints Twilio does:
 *   POST /voice/incoming  → welcome + language DTMF menu
 *   POST /voice/language  → language confirmed, open speech gather
 *   POST /voice/gather    → user spoke → async RAG+LLM processing
 *   POST /voice/poll      → waits for result, returns TTS audio
 *
 * No Twilio credits used. Full conversation history and language selection
 * work exactly as on the real phone number.
 */
import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Phone, PhoneOff, Mic, Volume2, RefreshCw, RotateCcw } from 'lucide-react'

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_BASE ||
  'https://e1oy2y9gjj.execute-api.us-east-1.amazonaws.com/prod'

const LANG_META = {
  hi: { label: 'हिंदी',   sub: 'Hindi',   sr: 'hi-IN', digit: '1' },
  mr: { label: 'मराठी',   sub: 'Marathi',  sr: 'mr-IN', digit: '2' },
  ta: { label: 'தமிழ்',  sub: 'Tamil',    sr: 'ta-IN', digit: '3' },
  en: { label: 'English', sub: 'English',  sr: 'en-IN', digit: '4' },
}

// ── TwiML XML parser ──────────────────────────────────────
function parseTwiML(xml) {
  try {
    const doc = new DOMParser().parseFromString(xml, 'text/xml')
    const resp = doc.querySelector('Response')
    if (!resp) return []
    return [...resp.childNodes]
      .filter(n => n.nodeType === 1) // Element nodes only
      .map(el => ({
        tag: el.tagName,
        text: el.textContent?.trim() || '',
        attrs: Object.fromEntries([...el.attributes].map(a => [a.name, a.value])),
        children: [...el.childNodes]
          .filter(c => c.nodeType === 1)
          .map(c => ({
            tag: c.tagName,
            text: c.textContent?.trim() || '',
            attrs: Object.fromEntries([...c.attributes].map(a => [a.name, a.value])),
          })),
      }))
  } catch {
    return []
  }
}

export default function PhoneSimulatorPage() {
  // ── UI state ──────────────────────────────────────────
  const [phase, setPhase] = useState('idle')
  // idle | ringing | language-select | listening | thinking | speaking | ended | error
  const [messages, setMessages] = useState([])
  const [statusText, setStatusText] = useState('Ready — press Call to start')
  const [liveText, setLiveText] = useState('')   // live interim transcript
  const [activeLang, setActiveLang] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [errorMsg, setErrorMsg] = useState('')

  // ── Refs (mutable, don't trigger re-renders) ──────────
  const callActiveRef = useRef(false)
  const callSidRef    = useRef(null)
  const langRef       = useRef('hi')
  const phaseRef      = useRef('idle')
  const recognitionRef    = useRef(null)
  const audioRef          = useRef(null)
  const resolveDTMFRef    = useRef(null)
  const resolveSpeechRef  = useRef(null)
  const timerRef          = useRef(null)
  const msgBottomRef      = useRef(null)

  // Auto-scroll chat to bottom
  useEffect(() => {
    msgBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, liveText, phase])

  // ── Helpers ───────────────────────────────────────────
  const setCallPhase = (p) => { phaseRef.current = p; setPhase(p) }

  const addMsg = useCallback((role, text, meta = {}) => {
    if (!text?.trim()) return
    setMessages(prev => [
      ...prev,
      { role, text: text.trim(), id: `${Date.now()}-${Math.random()}`, ...meta },
    ])
  }, [])

  // ── POST to a TwiML endpoint ──────────────────────────
  const postTwiML = useCallback(async (url, extra = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_BASE}${url}`
    const formBody = new URLSearchParams({
      CallSid: callSidRef.current ?? 'browser-sim',
      lang: langRef.current,
      From: '+910000000000',
      ...extra,
    }).toString()
    const res = await fetch(fullUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formBody,
    })
    if (!res.ok) throw new Error(`HTTP ${res.status} from ${fullUrl}`)
    return await res.text() // TwiML XML
  }, [])

  // ── Play an audio URL (no crossOrigin → works with S3 presigned URLs) ──
  const playAudio = useCallback((url) => {
    return new Promise(resolve => {
      if (!callActiveRef.current) { resolve(); return }
      const audio = new Audio(url)
      audioRef.current = audio
      let settled = false
      const done = () => { if (!settled) { settled = true; audioRef.current = null; resolve() } }
      audio.onended = done
      audio.onerror = done   // graceful — audio may be blocked; call continues
      audio.play().catch(done)
    })
  }, [])

  // ── Browser TTS fallback when audio can't play ────────
  const speakFallback = useCallback((text) => {
    return new Promise(resolve => {
      if (!callActiveRef.current || !text) { resolve(); return }
      window.speechSynthesis.cancel()
      const u = new SpeechSynthesisUtterance(text)
      u.lang = LANG_META[langRef.current]?.sr ?? 'hi-IN'
      u.rate = 1.1
      u.onend = resolve
      u.onerror = resolve
      const voices = window.speechSynthesis.getVoices()
      const match = voices.find(v => v.lang.startsWith(u.lang.slice(0, 2)))
      if (match) u.voice = match
      window.speechSynthesis.speak(u)
    })
  }, [])

  // ── Speak a TwiML Say/Play child set ──────────────────
  const speakNode = useCallback(async (node) => {
    if (!callActiveRef.current) return
    if (node.tag === 'Play') {
      setCallPhase('speaking')
      await playAudio(node.text)
    } else if (node.tag === 'Say') {
      setCallPhase('speaking')
      addMsg('ai', node.text)
      await speakFallback(node.text)
    }
  }, [playAudio, speakFallback, addMsg])

  // ── Wait for a DTMF digit button press ───────────────
  const waitForDTMF = () => new Promise(resolve => { resolveDTMFRef.current = resolve })

  const pressDigit = useCallback((digit) => {
    if (resolveDTMFRef.current) {
      resolveDTMFRef.current(digit)
      resolveDTMFRef.current = null
    }
  }, [])

  // ── Wait for browser SpeechRecognition ───────────────
  const waitForSpeech = () => new Promise(resolve => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      setStatusText('⚠ SpeechRecognition not supported — use Chrome')
      resolve('')
      return
    }
    const r = new SR()
    r.lang = LANG_META[langRef.current]?.sr ?? 'hi-IN'
    r.interimResults = true
    r.continuous = false
    recognitionRef.current = r

    let finalText = ''
    let done = false
    const finish = (text) => {
      if (!done) { done = true; setLiveText(''); resolve(text) }
    }

    r.onresult = (e) => {
      const all = [...e.results]
      setLiveText(all.map(r => r[0].transcript).join(''))
      const finals = all.filter(r => r.isFinal).map(r => r[0].transcript)
      if (finals.length) finalText = finals.join('')
    }
    r.onend = () => finish(finalText)
    r.onerror = (e) => {
      console.warn('SR error:', e.error)
      finish(finalText || '')
    }

    // External abort (End Call)
    resolveSpeechRef.current = (text) => { try { r.stop() } catch {} ; finish(text ?? '') }
    try { r.start() } catch { finish('') }
  })

  // ── Core TwiML execution engine ───────────────────────
  const executeTwiML = useCallback(async (xmlText) => {
    if (!callActiveRef.current) return
    const nodes = parseTwiML(xmlText)

    for (const node of nodes) {
      if (!callActiveRef.current) return

      // ── <Play> ──────────────────────────────────────
      if (node.tag === 'Play') {
        setCallPhase('speaking')
        setStatusText('VaaniSeva is speaking…')
        addMsg('ai', '🔊  (audio reply playing)', { isAudio: true })
        await playAudio(node.text)

      // ── <Say> ───────────────────────────────────────
      } else if (node.tag === 'Say') {
        // Only speak a top-level <Say> if there's no sibling <Play>
        if (!nodes.some(n => n.tag === 'Play')) {
          setCallPhase('speaking')
          setStatusText('VaaniSeva is speaking…')
          addMsg('ai', node.text)
          await speakFallback(node.text)
        }

      // ── <Redirect> ──────────────────────────────────
      } else if (node.tag === 'Redirect') {
        if (!callActiveRef.current) return
        setCallPhase('thinking')
        setStatusText('Processing with RAG + LLM…')
        const xml = await postTwiML(node.text)
        await executeTwiML(xml)
        return

      // ── <Gather> ────────────────────────────────────
      } else if (node.tag === 'Gather') {
        // First, play any nested Say/Play children (prompts inside Gather)
        for (const child of node.children) {
          if (!callActiveRef.current) return
          await speakNode(child)
          if (child.tag === 'Say' && !node.children.some(c => c.tag === 'Play')) {
            // text was already spoken by speakNode; show in transcript handled inside speakNode
          }
        }
        if (!callActiveRef.current) return

        const inputType = node.attrs.input ?? 'dtmf'
        const actionUrl = node.attrs.action ?? '/voice/gather'

        // ── DTMF: language selection keypad ───────────
        if (inputType.includes('dtmf')) {
          setCallPhase('language-select')
          setStatusText('Press 1–4 to choose your language')
          const digit = await waitForDTMF()
          if (!callActiveRef.current || digit === null) return

          const newLang = { '1': 'hi', '2': 'mr', '3': 'ta', '4': 'en' }[digit] ?? 'hi'
          langRef.current = newLang
          setActiveLang(newLang)
          addMsg('system', `Language selected: ${LANG_META[newLang].sub} (pressed ${digit})`)
          setCallPhase('thinking')
          setStatusText('Connecting…')
          const xml = await postTwiML(actionUrl, { Digits: digit })
          await executeTwiML(xml)
          return

        // ── Speech: mic input ──────────────────────────
        } else {
          setCallPhase('listening')
          setStatusText('Listening… speak now')
          const spokenText = await waitForSpeech()
          if (!callActiveRef.current) return

          if (spokenText) addMsg('user', spokenText)
          setCallPhase('thinking')
          setStatusText('VaaniSeva is thinking…')
          const xml = await postTwiML(actionUrl, {
            SpeechResult: spokenText,
            Confidence: spokenText ? '0.9' : '0',
          })
          await executeTwiML(xml)
          return
        }
      }
    }
  }, [postTwiML, playAudio, speakFallback, speakNode, addMsg])

  // ── Start call ────────────────────────────────────────
  const startCall = useCallback(async () => {
    callSidRef.current = `browser-${Date.now()}`
    callActiveRef.current = true
    langRef.current = 'hi'
    setMessages([])
    setActiveLang(null)
    setLiveText('')
    setElapsed(0)
    setErrorMsg('')
    setCallPhase('ringing')
    setStatusText('Calling VaaniSeva…')

    timerRef.current = setInterval(() => setElapsed(s => s + 1), 1000)

    try {
      // POST to /voice/incoming — same as what Twilio does when call arrives
      const xml = await postTwiML('/voice/incoming', { From: '+910000000000' })
      if (callActiveRef.current) await executeTwiML(xml)
    } catch (err) {
      if (callActiveRef.current) {
        setCallPhase('error')
        setErrorMsg(err.message)
        setStatusText('Connection failed')
        callActiveRef.current = false
        clearInterval(timerRef.current)
      }
    }
  }, [postTwiML, executeTwiML])

  // ── End call ──────────────────────────────────────────
  const endCall = useCallback(() => {
    callActiveRef.current = false
    clearInterval(timerRef.current)
    if (recognitionRef.current)  { try { recognitionRef.current.stop() } catch {} }
    if (audioRef.current)        { try { audioRef.current.pause() } catch {} ; audioRef.current = null }
    if (resolveDTMFRef.current)  { resolveDTMFRef.current(null); resolveDTMFRef.current = null }
    if (resolveSpeechRef.current){ resolveSpeechRef.current('');  resolveSpeechRef.current = null }
    window.speechSynthesis.cancel()
    setCallPhase('ended')
    setStatusText('Call ended')
    setLiveText('')
  }, [])

  const fmtElapsed = (s) =>
    `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

  const isOnCall = ['ringing', 'language-select', 'listening', 'thinking', 'speaking'].includes(phase)

  // Phase colors / labels for status chip
  const phaseChip = {
    ringing:         { bg: 'bg-gray-700',    color: 'text-gray-300',  label: '~ Calling' },
    'language-select':{ bg: 'bg-purple-900', color: 'text-purple-300', label: '# Select Language' },
    listening:       { bg: 'bg-green-900',   color: 'text-green-300',  label: '● Listening' },
    thinking:        { bg: 'bg-yellow-900',  color: 'text-yellow-300', label: '⟳ Thinking' },
    speaking:        { bg: 'bg-blue-900',    color: 'text-blue-300',   label: '▶ Speaking' },
  }[phase] ?? {}

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-start py-8 px-4 gap-4">

      {/* ── Page header ─────────────────────────────────── */}
      <div className="text-center">
        <h1 className="text-white font-bold text-xl tracking-tight">
          VaaniSeva Phone Simulator
        </h1>
        <p className="text-white/40 text-xs mt-1">
          Tests the <span className="text-green-400">exact same Lambda</span> as the Twilio number — zero credits used
        </p>
      </div>

      {/* ── Phone frame ─────────────────────────────────── */}
      <div className="relative w-[360px] bg-gray-900 rounded-[44px] shadow-2xl border border-gray-700 overflow-hidden flex flex-col"
           style={{ height: 720 }}>

        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-7 bg-gray-900 rounded-b-3xl z-10" />

        {/* Status bar */}
        <div className="flex items-center justify-between px-8 pt-3 pb-0 text-white/30 text-[11px] flex-shrink-0">
          <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          <span>📶</span>
        </div>

        {/* Call header */}
        <div className="px-5 pt-2 pb-3 flex items-center gap-3 flex-shrink-0 border-b border-gray-800">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xl transition-colors
            ${phase === 'listening' ? 'bg-green-700 animate-pulse' :
              phase === 'thinking'  ? 'bg-yellow-700' :
              phase === 'speaking'  ? 'bg-blue-700' : 'bg-gray-700'}`}>
            {phase === 'listening' ? '🎙️' : phase === 'speaking' ? '🔊' : '🤖'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white font-semibold text-sm">VaaniSeva</p>
            <p className="text-white/40 text-xs truncate">
              {isOnCall
                ? `${fmtElapsed(elapsed)}${activeLang ? ` · ${LANG_META[activeLang]?.sub}` : ''}`
                : 'VaaniSeva AI · Rural India'}
            </p>
          </div>
          {isOnCall && phaseChip.label && (
            <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium ${phaseChip.bg} ${phaseChip.color}`}>
              {phaseChip.label}
            </span>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2 min-h-0">
          {messages.length === 0 && !isOnCall && (
            <div className="text-center text-white/25 text-sm pt-12">
              <div className="text-5xl mb-4">📞</div>
              <p className="font-medium">Press Call to start</p>
              <p className="text-xs mt-2 leading-relaxed text-white/15">
                Hits the real Lambda. Full DTMF language selection.<br/>
                Speech flows through RAG + LLM + Sarvam TTS.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : msg.role === 'system' ? 'justify-center' : 'justify-start'}`}>
              {msg.role === 'system' ? (
                <span className="text-white/30 text-[11px] bg-gray-800 px-3 py-1 rounded-full">{msg.text}</span>
              ) : (
                <div className={`max-w-[78%] px-3 py-2 rounded-2xl text-sm leading-relaxed
                  ${msg.role === 'user'
                    ? 'bg-green-700 text-white rounded-br-sm'
                    : msg.isAudio
                      ? 'bg-gray-700/50 text-white/50 rounded-bl-sm italic text-xs border border-gray-700'
                      : 'bg-gray-700 text-white/90 rounded-bl-sm'}`}>
                  {msg.text}
                </div>
              )}
            </div>
          ))}

          {/* Live transcript bubble */}
          {liveText && (
            <div className="flex justify-end">
              <div className="max-w-[78%] px-3 py-2 rounded-2xl rounded-br-sm bg-green-900/40 text-green-300 text-sm italic border border-green-800/50">
                {liveText}…
              </div>
            </div>
          )}

          {/* Thinking dots */}
          {phase === 'thinking' && (
            <div className="flex justify-start">
              <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-gray-700 flex items-center gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }} />
                ))}
              </div>
            </div>
          )}

          {/* Error chip */}
          {phase === 'error' && errorMsg && (
            <div className="bg-red-900/40 border border-red-800/50 rounded-xl p-3 text-red-300 text-xs text-center">
              ⚠ {errorMsg}
            </div>
          )}

          <div ref={msgBottomRef} />
        </div>

        {/* Status text */}
        <div className="px-5 py-1 text-center flex-shrink-0">
          <p className="text-white/35 text-[11px] truncate">{statusText}</p>
        </div>

        {/* ── Bottom controls ──────────────────────────────── */}
        <div className="px-5 pb-8 pt-1 flex-shrink-0">

          {/* IDLE / ENDED / ERROR → green call button */}
          {(phase === 'idle' || phase === 'ended' || phase === 'error') && (
            <button onClick={startCall}
              className="w-full py-4 bg-green-600 hover:bg-green-500 active:scale-95 text-white font-bold text-base rounded-2xl flex items-center justify-center gap-3 transition-all shadow-lg shadow-green-900/30">
              <Phone size={20} />
              {phase === 'ended' ? 'Call Again' : 'Start Call'}
            </button>
          )}

          {/* LANGUAGE-SELECT → language buttons + full keypad */}
          {phase === 'language-select' && (
            <div className="space-y-2">
              <p className="text-white/40 text-xs text-center">Press to select language</p>
              <div className="grid grid-cols-2 gap-2">
                {[['1','hi'], ['2','mr'], ['3','ta'], ['4','en']].map(([digit, lang]) => (
                  <button key={digit} onClick={() => pressDigit(digit)}
                    className="py-3 bg-gray-700 hover:bg-gray-600 active:scale-95 rounded-xl text-center transition-all">
                    <span className="text-white/40 text-xs block">{digit}</span>
                    <span className="text-white font-bold text-sm">{LANG_META[lang].label}</span>
                    <span className="text-white/35 text-xs block">{LANG_META[lang].sub}</span>
                  </button>
                ))}
              </div>
              {/* Remaining keypad keys */}
              <div className="grid grid-cols-3 gap-1.5">
                {['5','6','7','8','9',  '*','0','#'].map(d => (
                  <button key={d} onClick={() => pressDigit(d)}
                    className="py-2 bg-gray-800 hover:bg-gray-700 rounded-xl text-white text-sm transition-colors">
                    {d}
                  </button>
                ))}
              </div>
              <button onClick={endCall}
                className="w-full py-3 bg-red-700 hover:bg-red-600 active:scale-95 text-white font-bold rounded-2xl flex items-center justify-center gap-2 transition-all">
                <PhoneOff size={18} /> End Call
              </button>
            </div>
          )}

          {/* ACTIVE CALL (listening / thinking / speaking / ringing) */}
          {(['ringing', 'listening', 'thinking', 'speaking'].includes(phase)) && (
            <div className="space-y-3">
              {/* Visual indicator */}
              <div className="flex justify-center items-end gap-1 h-10">
                {phase === 'listening' && [...Array(9)].map((_, i) => (
                  <div key={i} className="w-1.5 bg-green-400 rounded-full animate-pulse"
                    style={{ height: `${20 + Math.abs(Math.sin(i)) * 28}px`, animationDelay: `${i * 80}ms`, animationDuration: '0.7s' }} />
                ))}
                {phase === 'speaking' && [...Array(9)].map((_, i) => (
                  <div key={i} className="w-1.5 bg-blue-400 rounded-full animate-pulse"
                    style={{ height: `${15 + Math.abs(Math.cos(i * 0.8)) * 32}px`, animationDelay: `${i * 60}ms`, animationDuration: '0.9s' }} />
                ))}
                {phase === 'thinking' && (
                  <div className="flex items-center gap-2">
                    <RefreshCw size={18} className="text-yellow-400 animate-spin" />
                    <span className="text-yellow-400/70 text-xs">RAG + LLM + TTS…</span>
                  </div>
                )}
                {phase === 'ringing' && (
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-400 rounded-full animate-ping" />
                    <span className="text-green-400/70 text-xs">Connecting to Lambda…</span>
                  </div>
                )}
              </div>

              {/* Phase hint */}
              <p className="text-center text-white/30 text-xs">
                {phase === 'listening' && `Speak in ${activeLang ? LANG_META[activeLang].sub : 'your language'}…`}
                {phase === 'thinking'  && 'Searching knowledge base, generating reply…'}
                {phase === 'speaking'  && 'Playing Sarvam TTS response…'}
                {phase === 'ringing'   && 'Initialising VaaniSeva call session…'}
              </p>

              <button onClick={endCall}
                className="w-full py-4 bg-red-700 hover:bg-red-600 active:scale-95 text-white font-bold text-base rounded-2xl flex items-center justify-center gap-3 transition-all shadow-lg shadow-red-900/30">
                <PhoneOff size={20} /> End Call
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Info panel below phone ───────────────────────── */}
      <div className="w-[360px] bg-gray-900/50 border border-gray-800 rounded-2xl p-4 text-xs text-white/40 space-y-1.5">
        <p className="text-white/60 font-semibold text-sm mb-2">How this works</p>
        <p>1. Hits <code className="text-green-400">/voice/incoming</code> — same as Twilio inbound call</p>
        <p>2. DTMF 1/2/3/4 → <code className="text-green-400">/voice/language</code> — sets language in DynamoDB</p>
        <p>3. Browser mic → <code className="text-green-400">/voice/gather</code> — triggers async RAG+LLM</p>
        <p>4. <code className="text-green-400">/voice/poll</code> — waits for result, plays Sarvam TTS audio</p>
        <p className="text-yellow-400/60 pt-1">⚠ Use Chrome. Language selection is real — session is stored in DynamoDB.</p>
      </div>
    </div>
  )
}
