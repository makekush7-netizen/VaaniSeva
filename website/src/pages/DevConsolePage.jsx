/**
 * DevConsolePage — Continuous voice agent (browser SpeechRecognition + /chat + TTS)
 *
 * STT : browser SpeechRecognition (Chrome built-in, instant, free)
 * LLM : POST /chat  →  VaaniSeva Lambda
 * TTS : audio_url from Sarvam, or browser speechSynthesis fallback
 *
 * Route: /dev  — dev tool, not in main nav
 */
import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Phone, PhoneOff, Mic, MicOff, Volume2, ChevronDown, Trash2 } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const SR       = window.SpeechRecognition || window.webkitSpeechRecognition

const LANGUAGES = [
  { code: 'hi', label: 'हिंदी',  full: 'हिंदी (Hindi)',    srCode: 'hi-IN', flag: '🇮🇳' },
  { code: 'mr', label: 'मराठी', full: 'मराठी (Marathi)', srCode: 'mr-IN', flag: '🇮🇳' },
  { code: 'ta', label: 'தமிழ்', full: 'தமிழ் (Tamil)',   srCode: 'ta-IN', flag: '🇮🇳' },
  { code: 'en', label: 'EN',    full: 'English',          srCode: 'en-IN', flag: '🇬🇧' },
]

async function speakWithBrowser(text, langCode) {
  return new Promise(resolve => {
    if (!window.speechSynthesis) return resolve()
    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang  = { hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN', en: 'en-IN' }[langCode] || 'hi-IN'
    utt.rate  = 0.92
    utt.pitch = 1.05
    utt.onend = resolve; utt.onerror = resolve
    window.speechSynthesis.speak(utt)
  })
}

const STATES = {
  idle:       { ring: 'ring-gray-600',   pulse: false, label: 'Press call to start',    emoji: '🤖', color: 'text-gray-400'   },
  listening:  { ring: 'ring-green-500',  pulse: true,  label: 'Listening… speak now',   emoji: '👂', color: 'text-green-400'  },
  speaking:   { ring: 'ring-red-500',    pulse: true,  label: 'You are speaking…',       emoji: '🎤', color: 'text-red-400'    },
  thinking:   { ring: 'ring-blue-400',   pulse: true,  label: 'VaaniSeva is thinking…',  emoji: '🤔', color: 'text-blue-400'   },
  responding: { ring: 'ring-violet-500', pulse: true,  label: 'VaaniSeva is speaking…',  emoji: '🔊', color: 'text-violet-400' },
  error:      { ring: 'ring-red-600',    pulse: false, label: 'Error — try again',       emoji: '⚠️', color: 'text-red-400'    },
}

// ── Animated avatar ─────────────────────────────────────────────────────────────
function Avatar({ callState, audioLevel }) {
  const s = STATES[callState] || STATES.idle
  const r = 40 + audioLevel * 0.25
  return (
    <div className="relative flex items-center justify-center" style={{ width: 200, height: 200 }}>
      {s.pulse && [1.6, 2.0, 2.4].map((m, i) => (
        <div key={i} className="absolute rounded-full border opacity-[0.12] transition-all duration-150"
          style={{
            width: `${r * m}px`, height: `${r * m}px`,
            borderColor: callState === 'speaking' ? '#ef4444' : callState === 'responding' ? '#a78bfa' : '#4ade80',
          }}
        />
      ))}
      {s.pulse && (
        <div className={`absolute w-24 h-24 rounded-full ${s.ring} ring-4 animate-ping opacity-[0.15]`} />
      )}
      <div className={`relative z-10 w-24 h-24 rounded-full bg-gray-800 ring-4 ${s.ring} flex items-center justify-center transition-all duration-300 shadow-2xl`}>
        <span style={{ fontSize: 42 }}>{s.emoji}</span>
      </div>
    </div>
  )
}

// ── Message bubble ───────────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-2.5`}>
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-violet-900 text-xs flex items-center justify-center mr-2 mt-1 flex-shrink-0">🤖</div>
      )}
      <div className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
        isUser
          ? 'bg-blue-600 bg-opacity-30 text-blue-100 border border-blue-500 border-opacity-30 rounded-br-sm'
          : 'bg-white bg-opacity-10 text-gray-100 border border-white border-opacity-10 rounded-bl-sm'
      }`}>
        <p>{msg.text}</p>
        <p className="text-[10px] mt-1 opacity-30">{msg.time}</p>
      </div>
      {isUser && (
        <div className="w-6 h-6 rounded-full bg-blue-900 text-xs flex items-center justify-center ml-2 mt-1 flex-shrink-0">👤</div>
      )}
    </div>
  )
}

// ── Main component ───────────────────────────────────────────────────────────────
export default function DevConsolePage() {
  const [callState, setCallState]   = useState('idle')
  const [language,  setLanguage]    = useState('hi')
  const [messages,  setMessages]    = useState([])
  const [audioLevel, setAudioLevel] = useState(0)
  const [muted,      setMuted]      = useState(false)
  const [errorMsg,   setErrorMsg]   = useState('')
  const [interimText, setInterimText] = useState('')
  const [langOpen,   setLangOpen]   = useState(false)

  const callActiveRef   = useRef(false)
  const callStateRef    = useRef('idle')
  const languageRef     = useRef('hi')
  const mutedRef        = useRef(false)
  const sessionRef      = useRef(`dev-${Date.now()}`)
  const recognitionRef  = useRef(null)
  const listeningRef    = useRef(false)  // should recognition be running?
  const processingRef   = useRef(false)  // chat request in-flight?
  const streamRef       = useRef(null)
  const audioCtxRef     = useRef(null)
  const analyserRef     = useRef(null)
  const dataArrRef      = useRef(null)
  const rafRef          = useRef(null)
  const chatBottomRef   = useRef(null)

  useEffect(() => { languageRef.current = language }, [language])
  useEffect(() => { mutedRef.current = muted }, [muted])
  useEffect(() => { chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => () => { stopAll() }, [])

  const setCS = (s) => { callStateRef.current = s; setCallState(s) }

  const addMessage = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setMessages(prev => [...prev, { id: `${Date.now()}-${Math.random()}`, role, text, time }])
  }, [])

  // ── Resume SpeechRecognition ────────────────────────────────────────────────
  const resumeListening = useCallback(() => {
    if (!callActiveRef.current || !recognitionRef.current) return
    listeningRef.current = true
    try { recognitionRef.current.start() } catch (_) {}
  }, [])

  // ── Play TTS response, then resume listening ────────────────────────────────
  const playAndListen = useCallback(async (answer, audioUrl, lang) => {
    setCS('responding')
    try {
      if (audioUrl) {
        await new Promise(resolve => {
          const a = new Audio(audioUrl)
          a.onended = resolve; a.onerror = resolve
          a.play().catch(resolve)
        })
      } else {
        await speakWithBrowser(answer, lang || languageRef.current)
      }
    } catch (_) {}
    if (callActiveRef.current) {
      processingRef.current = false
      setCS('listening')
      setInterimText('')
      setTimeout(resumeListening, 350)  // brief gap so mic doesn't catch TTS echo
    }
  }, [resumeListening])

  // ── POST /chat ──────────────────────────────────────────────────────────────
  const sendToChat = useCallback(async (transcript) => {
    if (!callActiveRef.current || !transcript.trim()) return
    setCS('thinking')
    setInterimText('')
    addMessage('user', transcript)
    setErrorMsg('')
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: transcript,
          language: languageRef.current,
          session_id: sessionRef.current,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Chat request failed')
      const answer = data.answer || data.response || '(no response)'
      addMessage('assistant', answer)
      await playAndListen(answer, data.audio_url || '', data.language || languageRef.current)
    } catch (err) {
      setErrorMsg(err.message)
      processingRef.current = false
      if (callActiveRef.current) {
        setCS('listening')
        setTimeout(resumeListening, 400)
      }
    }
  }, [addMessage, playAndListen, resumeListening])

  // ── Create SpeechRecognition object ────────────────────────────────────────
  const buildRecognition = useCallback((srCode) => {
    const r = new SR()
    r.continuous      = true
    r.interimResults  = true
    r.lang            = srCode
    r.maxAlternatives = 1

    r.onresult = (event) => {
      if (mutedRef.current || !callActiveRef.current || processingRef.current) return
      let interim = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          const text = result[0].transcript.trim()
          if (text && callActiveRef.current && !processingRef.current) {
            processingRef.current = true
            listeningRef.current  = false
            try { r.stop() } catch (_) {}
            sendToChat(text)
            return
          }
        } else {
          interim += result[0].transcript
        }
      }
      if (interim && callStateRef.current === 'listening') {
        setCS('speaking')
        setInterimText(interim)
      }
    }

    r.onspeechend = () => {
      // This fires when speech stops but before final result — just wait for onresult
    }

    r.onerror = (e) => {
      if (e.error === 'no-speech' || e.error === 'aborted') return  // normal
      if (e.error === 'network') {
        setErrorMsg('Network error in speech recognition. Check internet.')
        return
      }
      console.warn('[SR error]', e.error)
    }

    r.onend = () => {
      // If we should still be listening (e.g. utterance ended, no final result yet)
      if (listeningRef.current && callActiveRef.current && !processingRef.current) {
        if (['speaking', 'listening'].includes(callStateRef.current)) setCS('listening')
        setTimeout(() => {
          if (listeningRef.current && callActiveRef.current) {
            try { r.start() } catch (_) {}
          }
        }, 200)
      }
    }

    return r
  }, [sendToChat])

  // ── Mic level animation (AudioContext — visual only) ────────────────────────
  const startLevelMeter = useCallback(() => {
    const tick = () => {
      if (!callActiveRef.current) return
      const analyser = analyserRef.current
      const arr      = dataArrRef.current
      if (analyser && arr) {
        analyser.getByteTimeDomainData(arr)
        let s = 0
        for (let i = 0; i < arr.length; i++) { const v = (arr[i] - 128) / 128; s += v * v }
        setAudioLevel(Math.min(100, (Math.sqrt(s / arr.length) / 0.05) * 100))
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
  }, [])

  // ── Start call ──────────────────────────────────────────────────────────────
  const startCall = async () => {
    setErrorMsg('')
    if (!SR) {
      setErrorMsg('Speech recognition not supported. Use Google Chrome.')
      setCS('error')
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current  = stream

      // AudioContext for mic level animation only
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      if (ctx.state === 'suspended') await ctx.resume()
      audioCtxRef.current = ctx
      const src = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 512
      analyser.smoothingTimeConstant = 0.4
      src.connect(analyser)
      analyserRef.current = analyser
      dataArrRef.current  = new Uint8Array(analyser.fftSize)

      callActiveRef.current  = true
      processingRef.current  = false
      listeningRef.current   = true
      sessionRef.current     = `dev-${Date.now()}`
      setMuted(false); mutedRef.current = false

      const lang = LANGUAGES.find(l => l.code === languageRef.current)
      const r    = buildRecognition(lang?.srCode || 'hi-IN')
      recognitionRef.current = r
      r.start()

      setCS('listening')
      startLevelMeter()
    } catch (err) {
      setErrorMsg(
        err.name === 'NotAllowedError'
          ? 'Microphone access denied. Allow mic in browser settings.'
          : `Mic error: ${err.message}`
      )
      setCS('error')
    }
  }

  // ── Stop all ────────────────────────────────────────────────────────────────
  const stopAll = () => {
    callActiveRef.current = false
    listeningRef.current  = false
    processingRef.current = false
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    try { recognitionRef.current?.abort() } catch (_) {}
    streamRef.current?.getTracks().forEach(t => t.stop())
    if (audioCtxRef.current?.state !== 'closed') audioCtxRef.current?.close().catch(() => {})
    window.speechSynthesis?.cancel()
  }

  const endCall = () => {
    stopAll()
    setCallState('idle'); callStateRef.current = 'idle'
    setAudioLevel(0); setInterimText(''); setErrorMsg('')
  }

  const toggleMute = () => {
    const next = !muted
    setMuted(next); mutedRef.current = next
    streamRef.current?.getAudioTracks().forEach(t => { t.enabled = !next })
    if (next) {
      listeningRef.current = false
      try { recognitionRef.current?.stop() } catch (_) {}
    } else if (callActiveRef.current && !processingRef.current) {
      setTimeout(() => { listeningRef.current = true; resumeListening() }, 200)
    }
  }

  const isOnCall = !['idle', 'error'].includes(callState)
  const currentLang = LANGUAGES.find(l => l.code === language)
  const st = STATES[callState] || STATES.idle

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col select-none">

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-lg">🎙️</span>
          <div>
            <p className="text-sm font-semibold leading-tight">VaaniSeva Dev Console</p>
            <p className="text-xs text-gray-500">
              {SR ? 'Browser STT → /chat → TTS · no Twilio' : '⚠️ Use Chrome for speech recognition'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <button
              onClick={() => setLangOpen(o => !o)}
              disabled={isOnCall}
              className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/10 hover:bg-white/20 disabled:opacity-40 rounded-lg text-xs font-medium transition-colors"
            >
              <span>{currentLang?.flag}</span>
              <span>{currentLang?.label}</span>
              <ChevronDown size={11} />
            </button>
            {langOpen && (
              <div className="absolute right-0 top-9 bg-gray-800 border border-white/10 rounded-xl shadow-2xl z-50 min-w-[180px]">
                {LANGUAGES.map(l => (
                  <button key={l.code}
                    onClick={() => { setLanguage(l.code); setLangOpen(false) }}
                    className={`w-full text-left px-3.5 py-2.5 text-sm hover:bg-white/10 flex items-center gap-2 first:rounded-t-xl last:rounded-b-xl transition-colors ${
                      l.code === language ? 'text-green-400 font-semibold' : 'text-gray-200'
                    }`}
                  >
                    <span>{l.flag}</span><span>{l.full}</span>
                    {l.code === language && <span className="ml-auto text-green-400 text-xs">✓</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => setMessages([])} title="Clear" className="p-1.5 text-gray-600 hover:text-gray-300">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* ── Avatar + status ── */}
      <div className="flex flex-col items-center pt-6 pb-3 flex-shrink-0">
        <Avatar callState={callState} audioLevel={audioLevel} />
        <p className={`text-sm font-semibold mt-2 transition-colors duration-300 ${st.color}`}>
          {st.label}
        </p>
        {errorMsg && (
          <p className="text-xs text-red-400 mt-1.5 text-center max-w-xs px-3">{errorMsg}</p>
        )}
        {isOnCall && (
          <div className="mt-2.5 w-48">
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-75 ${
                  callState === 'speaking' ? 'bg-red-500' : 'bg-green-500/60'
                }`}
                style={{ width: `${audioLevel}%` }}
              />
            </div>
            <p className="text-[10px] text-center text-gray-700 mt-1">
              {muted ? '🔴 Muted' : `Mic: ${Math.round(audioLevel)}%`}
            </p>
          </div>
        )}
      </div>

      {/* ── Chat history ── */}
      <div className="flex-1 overflow-y-auto px-4 pb-2 max-w-lg w-full mx-auto">
        {messages.length === 0 && !interimText && (
          <div className="text-center py-8 text-gray-700 text-sm">
            {isOnCall ? 'Speak naturally — VaaniSeva will reply automatically' : 'Press the green call button, then speak'}
          </div>
        )}
        {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}

        {/* Live interim transcript */}
        {interimText && (
          <div className="flex justify-end mb-2.5">
            <div className="max-w-[78%] rounded-2xl rounded-br-sm px-3.5 py-2.5 text-sm leading-relaxed bg-blue-600/15 text-blue-300/70 border border-blue-500/20 italic animate-pulse">
              {interimText}…
            </div>
            <div className="w-6 h-6 rounded-full bg-blue-900 text-xs flex items-center justify-center ml-2 mt-1 flex-shrink-0">👤</div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* ── Controls ── */}
      <div className="flex items-center justify-center gap-12 py-6 border-t border-white/10 flex-shrink-0">
        {isOnCall ? (
          <>
            {/* Mute */}
            <button
              onClick={toggleMute}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-lg ${
                muted
                  ? 'bg-amber-500/20 text-amber-400 ring-1 ring-amber-500/50'
                  : 'bg-white/10 text-gray-400 hover:bg-white/20 hover:text-white'
              }`}
            >
              {muted ? <MicOff size={20} /> : <Mic size={20} />}
            </button>

            {/* End call */}
            <button
              onClick={endCall}
              className="w-20 h-20 rounded-full bg-red-600 hover:bg-red-500 active:scale-95 flex items-center justify-center transition-all"
              style={{ boxShadow: '0 0 30px rgba(239,68,68,0.4)' }}
            >
              <PhoneOff size={28} className="text-white" />
            </button>

            {/* Speaker */}
            <div className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${
              callState === 'responding'
                ? 'bg-violet-500/20 text-violet-400 ring-1 ring-violet-500/50'
                : 'bg-white/10 text-gray-700'
            }`}>
              <Volume2 size={20} />
            </div>
          </>
        ) : (
          <button
            onClick={startCall}
            className="w-20 h-20 rounded-full bg-green-600 hover:bg-green-500 active:scale-95 flex items-center justify-center transition-all"
            style={{ boxShadow: '0 0 30px rgba(34,197,94,0.4)' }}
          >
            <Phone size={28} className="text-white" />
          </button>
        )}
      </div>

      <p className="text-center text-[10px] text-gray-800 pb-2">{API_BASE}</p>
    </div>
  )
}
