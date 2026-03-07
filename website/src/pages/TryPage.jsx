import React, { useState, useRef, useEffect } from 'react'
import { Phone, PhoneCall, PhoneOff, Mic, MicOff, Loader2, ArrowLeft, Send, Volume2, Keyboard, Delete } from 'lucide-react'
import { Link } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.DEV

// ══════════════════════════════════════════════════════
//  SECTION 1: Call Me Back
// ══════════════════════════════════════════════════════
export function CallMeBack({ compact = false }) {
  const [countryCode, setCountryCode] = useState('+91')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState('idle') // idle | sending | success | error
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!phone.trim()) return

    const cleanPhone = phone.replace(/[\s\-()]/g, '')
    if (cleanPhone.length < 7 || cleanPhone.length > 15) {
      setErrorMsg('Please enter a valid phone number')
      return
    }

    const fullNumber = `${countryCode}${cleanPhone}`
    setStatus('sending')
    setErrorMsg('')

    try {
      const res = await fetch(`${API_BASE}/call/initiate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: fullNumber }),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || 'Failed to initiate call')
      }

      setStatus('success')
    } catch (err) {
      console.error('[Call Initiate Error]', err)
      setStatus('error')
      setErrorMsg(err.message || 'Something went wrong. Please try again.')
    }
  }

  if (status === 'success') {
    return (
      <div className={`text-center ${compact ? 'py-6' : 'py-12'}`}>
        <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <PhoneCall size={28} className="text-green-500" />
        </div>
        <h3 className="text-lg font-bold text-content-primary mb-1">📞 Calling you now!</h3>
        <p className="text-sm text-content-secondary mb-1">
          Pick up in ~10 seconds!
        </p>
        <p className="font-hindi text-accent-600 text-xs mb-4">
          आपके नंबर पर कॉल आ रही है। कृपया कॉल उठाएं।
        </p>
        <button
          onClick={() => { setStatus('idle'); setPhone('') }}
          className="btn-secondary text-sm"
        >
          Request Another Call
        </button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className={compact ? 'space-y-3' : 'space-y-5'}>
      <div>
        <label className="block text-sm font-medium text-content-primary mb-1.5">
          Phone Number <span className="font-hindi text-content-secondary text-xs">— फ़ोन नंबर</span>
        </label>
        <div className="flex gap-2">
          <select
            value={countryCode}
            onChange={(e) => setCountryCode(e.target.value)}
            className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-3 text-sm text-content-primary font-mono outline-none focus:border-accent-500"
          >
            <option value="+91">🇮🇳 +91</option>
            <option value="+1">🇺🇸 +1</option>
            <option value="+44">🇬🇧 +44</option>
            <option value="+971">🇦🇪 +971</option>
            <option value="+65">🇸🇬 +65</option>
            <option value="+61">🇦🇺 +61</option>
            <option value="+880">🇧🇩 +880</option>
            <option value="+977">🇳🇵 +977</option>
          </select>
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="98765 43210"
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-accent-500 focus:ring-1 focus:ring-accent-500 outline-none transition-colors font-mono text-lg"
            maxLength={15}
          />
        </div>
      </div>

      {/* Error */}
      {(status === 'error' || errorMsg) && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-600">{errorMsg}</p>
        </div>
      )}

      <button
        type="submit"
        disabled={status === 'sending' || !phone.trim()}
        className="btn-primary w-full text-base py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {status === 'sending' ? (
          <><Loader2 size={18} className="animate-spin" /> Calling...</>
        ) : (
          <><Phone size={18} /> Call Me Now</>
        )}
      </button>

      {/* Disclaimer */}
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl">
        <p className="text-xs text-amber-700 leading-relaxed">
          <strong>Why a US number?</strong> VaaniSeva is in the trial phase for AI for Bharat Hackathon 2026.
          We are provisioning an Indian toll-free number — until it is active, calls are placed from our US Twilio
          number (+1 978 830 9619). <strong>The call is completely free on our end.</strong> Standard carrier rates
          may apply on your end for international calls. You can also use the Live Call tab above to talk directly
          from your browser — no phone needed.
        </p>
      </div>
    </form>
  )
}


// ══════════════════════════════════════════════════════
//  SECTION 2: Real Browser Voice Call (Twilio WebRTC)
// ══════════════════════════════════════════════════════

const KEYPAD_KEYS = [
  { digit: '1', sub: '' },
  { digit: '2', sub: 'ABC' },
  { digit: '3', sub: 'DEF' },
  { digit: '4', sub: 'GHI' },
  { digit: '5', sub: 'JKL' },
  { digit: '6', sub: 'MNO' },
  { digit: '7', sub: 'PQRS' },
  { digit: '8', sub: 'TUV' },
  { digit: '9', sub: 'WXYZ' },
  { digit: '*', sub: '' },
  { digit: '0', sub: '+' },
  { digit: '#', sub: '' },
]

function DialerKey({ digit, sub, onPress, active }) {
  const [pressed, setPressed] = useState(false)
  const handlePress = () => {
    if (!active) return
    setPressed(true)
    onPress(digit)
    setTimeout(() => setPressed(false), 120)
  }
  return (
    <button
      onPointerDown={handlePress}
      disabled={!active}
      className={`
        flex flex-col items-center justify-center
        w-full aspect-square rounded-2xl select-none
        transition-all duration-100
        ${active
          ? pressed
            ? 'bg-amber-500 text-white scale-95 shadow-inner'
            : 'bg-[#2a2a3a] hover:bg-[#383850] active:bg-amber-500 text-white shadow-md hover:shadow-lg'
          : 'bg-[#1e1e2a] text-gray-600 cursor-not-allowed'
        }
      `}
    >
      <span className="text-2xl font-semibold leading-none">{digit}</span>
      {sub && <span className="text-[9px] font-medium tracking-widest mt-0.5 opacity-60">{sub}</span>}
    </button>
  )
}

// ── Daily-quota helpers (localStorage, no login required) ──────────────────
const DAILY_LIMIT_SEC = 99999    // no limit — open for judges and testers
const LS_KEY          = 'vaaniseva_voice_usage'

function loadQuota() {
  try {
    const raw  = localStorage.getItem(LS_KEY)
    const data = raw ? JSON.parse(raw) : null
    const today = new Date().toISOString().slice(0, 10)
    if (data && data.date === today) return data.used   // seconds used today
  } catch {}
  return 0
}

function saveQuota(usedSeconds) {
  const today = new Date().toISOString().slice(0, 10)
  try { localStorage.setItem(LS_KEY, JSON.stringify({ date: today, used: usedSeconds })) } catch {}
}

function VoiceChat() {
  const [language, setLanguage]       = useState('hi')
  const [voice, setVoice]             = useState('arya')
  const [callStatus, setCallStatus]   = useState('idle')
  const [isMuted, setIsMuted]         = useState(false)
  const [duration, setDuration]       = useState(0)
  const [error, setError]             = useState('')
  const [dtmfDisplay, setDtmfDisplay] = useState('')
  const [showText, setShowText]       = useState(false)
  const [textInput, setTextInput]     = useState('')
  const [isSending, setIsSending]     = useState(false)
  const [messages, setMessages]       = useState([])
  const [quotaUsed, setQuotaUsed]     = useState(() => loadQuota())
  const [maxDuration, setMaxDuration] = useState(DAILY_LIMIT_SEC)

  const deviceRef      = useRef(null)
  const callRef        = useRef(null)
  const timerRef       = useRef(null)
  const messagesEndRef = useRef(null)
  const sessionIdRef   = useRef(crypto.randomUUID())
  const quotaUsedRef   = useRef(quotaUsed)

  const languages = [
    { code: 'hi', label: 'हिंदी', hint: 'हिंदी में बोलें' },
    { code: 'mr', label: 'मराठी', hint: 'मराठीत बोला' },
    { code: 'ta', label: 'தமிழ்', hint: 'தமிழில் பேசுங்கள்' },
    { code: 'en', label: 'English', hint: 'Speak in English' },
  ]

  const voices = [
    { code: 'arya',   label: 'Arya',   icon: '👩', hint: 'Female · Hindi' },
    { code: 'vidya',  label: 'Vidya',  icon: '👩', hint: 'Female · Health' },
    { code: 'hitesh', label: 'Hitesh', icon: '👨', hint: 'Male · Hindi' },
  ]

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => {
    return () => {
      callRef.current?.disconnect()
      deviceRef.current?.destroy()
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  // Sync ref so the interval closure can read latest quotaUsed
  useEffect(() => { quotaUsedRef.current = quotaUsed }, [quotaUsed])

  const fmt = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
  const quotaRemaining = Math.max(0, DAILY_LIMIT_SEC - quotaUsed)
  const quotaPercent   = Math.min(100, Math.round((quotaUsed / DAILY_LIMIT_SEC) * 100))
  const quotaExhausted = quotaRemaining === 0

  const cleanupCall = (addSeconds = 0) => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
    deviceRef.current?.destroy()
    deviceRef.current = null
    callRef.current   = null
    setIsMuted(false)
    setDtmfDisplay('')
    if (addSeconds > 0) {
      const newUsed = Math.min(DAILY_LIMIT_SEC, quotaUsedRef.current + addSeconds)
      setQuotaUsed(newUsed)
      saveQuota(newUsed)
    }
    setDuration(0)
  }

  const startCall = async () => {
    if (quotaExhausted) return
    setError('')
    setCallStatus('connecting')
    setDtmfDisplay('')

    try {
      const res  = await fetch(`${API_BASE}/voice/token?language=${language}`)
      const data = await res.json()

      // Backend 429 = server-side IP rate limit hit
      if (res.status === 429) {
        setError('daily_limit_exceeded')
        setCallStatus('error')
        return
      }
      if (!res.ok) throw new Error(data.error || 'Could not get call token')

      // Use server-side max_duration if provided, otherwise use remaining quota
      const serverMax = data.max_duration || DAILY_LIMIT_SEC
      const allowed   = Math.min(serverMax, quotaRemaining)
      setMaxDuration(allowed)

      const { Device } = await import('@twilio/voice-sdk')
      const device = new Device(data.token, { logLevel: 1, codecPreferences: ['opus', 'pcmu'] })
      device.on('error', (e) => { setError(e.message || 'Device error'); setCallStatus('error'); cleanupCall() })
      deviceRef.current = device

      const call = await device.connect({ params: { lang: language, voice } })
      callRef.current = call

      call.on('accept', () => {
        setCallStatus('connected')
        let elapsed = 0
        timerRef.current = setInterval(() => {
          elapsed += 1
          setDuration(elapsed)
          // Auto-hangup when this call would exhaust the quota
          if (elapsed >= allowed) {
            call.disconnect()
          }
        }, 1000)
      })
      call.on('disconnect', () => {
        const elapsed = duration   // captured via ref below
        setCallStatus('idle')
        cleanupCall(elapsed)
      })
      call.on('error', (e) => { setError(e.message || 'Call error'); setCallStatus('error'); cleanupCall() })

    } catch (err) {
      console.error('startCall error:', err)
      setError(err.message || 'Failed to connect. Please try again.')
      setCallStatus('error')
      cleanupCall()
    }
  }

  // Keep a ref to current duration so disconnect handler can read it
  const durationRef = useRef(0)
  useEffect(() => { durationRef.current = duration }, [duration])

  const endCall = () => {
    const elapsed = durationRef.current
    setCallStatus('disconnecting')
    callRef.current?.disconnect()
    cleanupCall(elapsed)
    setTimeout(() => setCallStatus('idle'), 400)
  }

  const toggleMute = () => {
    if (callRef.current) {
      const next = !isMuted
      callRef.current.mute(next)
      setIsMuted(next)
    }
  }

  const pressKey = (digit) => {
    if (isOnCall && callRef.current) {
      callRef.current.sendDigits(digit)
      setDtmfDisplay(prev => (prev + digit).slice(-10))
    }
  }

  const sendText = async () => {
    if (!textInput.trim()) return
    const query = textInput.trim()
    setTextInput('')
    setIsSending(true)
    setMessages(prev => [...prev, { role: 'user', text: query, ts: Date.now() }])
    try {
      const res  = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, language, session_id: sessionIdRef.current, voice }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', text: data.answer || '…', audioUrl: data.audio_url, ts: Date.now() }])
      if (data.audio_url) new Audio(data.audio_url).play().catch(() => {})
    } catch {
      setMessages(prev => [...prev, { role: 'system', text: 'Failed to send. Please try again.', ts: Date.now() }])
    }
    setIsSending(false)
  }

  const isOnCall     = callStatus === 'connected'
  const isConnecting = callStatus === 'connecting' || callStatus === 'disconnecting'
  const currentLang  = languages.find(l => l.code === language)

  // ── Text mode ──────────────────────────────────────────
  if (showText) {
    return (
      <div className="flex flex-col">
        <div className="min-h-[250px] max-h-[360px] overflow-y-auto mb-4 space-y-3 pr-1">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-40 text-content-tertiary">
              <Send size={28} className="mb-2 opacity-30" />
              <p className="text-sm">Type your question to get started</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'   ? 'bg-accent-500 text-white rounded-br-md' :
                msg.role === 'system' ? 'bg-red-50 text-red-700 border border-red-200' :
                                       'bg-gray-100 text-content-primary rounded-bl-md'
              }`}>
                <p className={language !== 'en' && msg.role === 'assistant' ? 'font-hindi' : ''}>{msg.text}</p>
                {msg.audioUrl && (
                  <button onClick={() => new Audio(msg.audioUrl).play()} className="mt-1.5 flex items-center gap-1 text-xs text-accent-500 hover:text-accent-600">
                    <Volume2 size={12} /> Play audio
                  </button>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="flex gap-2">
          <input
            type="text" value={textInput}
            onChange={e => setTextInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendText()}
            placeholder={
              language === 'hi' ? 'अपना सवाल यहाँ लिखें...' :
              language === 'mr' ? 'तुमचा प्रश्न इथे लिहा...' :
              language === 'ta' ? 'உங்கள் கேள்வியை இங்கே எழுதுங்கள்...' :
              'Type your question here...'
            }
            className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:border-accent-500 focus:ring-1 focus:ring-accent-500 transition-colors"
            disabled={isSending}
          />
          <button onClick={sendText} disabled={isSending || !textInput.trim()} className="btn-primary !px-4 disabled:opacity-50">
            {isSending ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
        <button
          onClick={() => setShowText(false)}
          className="mt-3 text-xs text-content-tertiary hover:text-content-primary flex items-center gap-1.5 self-start transition-colors"
        >
          <Phone size={12} /> Switch to voice call
        </button>
      </div>
    )
  }

  // ── Phone / Dialer UI ──────────────────────────────────
  return (
    <div className="flex flex-col items-center">

      {/* Language Tabs */}
      <div className="flex bg-gray-100 rounded-2xl p-1 mb-3 w-full max-w-sm">
        {languages.map(l => (
          <button
            key={l.code}
            onClick={() => setLanguage(l.code)}
            disabled={isOnCall || isConnecting}
            className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all disabled:opacity-40 ${
              language === l.code
                ? 'bg-white text-amber-700 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <span className={l.code !== 'en' ? 'font-hindi' : ''}>{l.label}</span>
          </button>
        ))}
      </div>

      {/* Voice Selector */}
      <div className="w-full max-w-sm mb-3">
        <p className="text-[10px] text-gray-400 text-center mb-1.5 tracking-wide uppercase">Choose Voice</p>
        <div className="flex bg-gray-100 rounded-2xl p-1">
          {voices.map(v => (
            <button
              key={v.code}
              onClick={() => setVoice(v.code)}
              disabled={isOnCall || isConnecting}
              className={`flex-1 flex flex-col items-center py-2 rounded-xl text-xs font-semibold transition-all disabled:opacity-40 ${
                voice === v.code
                  ? 'bg-white text-amber-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span>{v.icon} {v.label}</span>
              <span className="text-[9px] font-normal opacity-60 mt-0.5">{v.hint}</span>
            </button>
          ))}
        </div>
        {isOnCall && (
          <p className="text-[10px] text-amber-500 text-center mt-1">
            Say "change voice" / "आवाज़ बदलो" to switch mid-call
          </p>
        )}
      </div>

      {/* ── Quota-exhausted lock screen ── */}
      {quotaExhausted && !isOnCall && (
        <div className="w-full max-w-xs rounded-[2.5rem] overflow-hidden shadow-2xl mb-4" style={{ background: '#12121e', border: '6px solid #1e1e30' }}>
          <div className="px-6 pt-10 pb-12 flex flex-col items-center text-center" style={{ background: 'linear-gradient(160deg, #1a1a2e 0%, #12121e 100%)' }}>
            <div className="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center mb-4">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-gray-400">
                <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <p className="text-white text-base font-semibold mb-1">Daily limit reached</p>
            <p className="text-gray-400 text-xs leading-relaxed mb-4">
              You've used your 10 min / day free browser call allowance.<br/>Resets at midnight UTC.
            </p>
            <p className="text-amber-400 text-xs">Use <strong>Call Me Back</strong> for unlimited access, or try again tomorrow.</p>
          </div>
        </div>
      )}

      {/* ── Phone Frame ── */}
      {!quotaExhausted && (
      <div
        className="w-full max-w-xs rounded-[2.5rem] overflow-hidden shadow-2xl"
        style={{ background: '#12121e', border: '6px solid #1e1e30' }}
      >
        {/* ── Screen ── */}
        <div className="px-6 pt-8 pb-6" style={{ background: 'linear-gradient(160deg, #1a1a2e 0%, #12121e 100%)' }}>
          {/* Speaker grill */}
          <div className="flex justify-center mb-5">
            <div className="w-16 h-1 rounded-full bg-gray-700 opacity-60" />
          </div>

          {/* Caller info / status */}
          <div className="text-center mb-4 min-h-[80px] flex flex-col items-center justify-center">
            {callStatus === 'idle' && (
              <>
                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center mb-3 shadow-lg">
                  <Phone size={24} className="text-white" />
                </div>
                <p className={`text-white text-lg font-semibold ${language !== 'en' ? 'font-hindi' : ''}`}>
                  {currentLang?.hint}
                </p>
                <p className="text-gray-400 text-xs mt-1">VaaniSeva · AI Voice Assistant</p>
              </>
            )}

            {isConnecting && (
              <>
                <div className="relative w-14 h-14 rounded-full bg-amber-500 flex items-center justify-center mb-3 shadow-lg">
                  <span className="absolute inset-0 rounded-full bg-amber-400 animate-ping opacity-50" />
                  <Loader2 size={24} className="text-white animate-spin relative z-10" />
                </div>
                <p className="text-amber-400 text-lg font-semibold">Connecting…</p>
                <p className="text-gray-400 text-xs mt-1">Setting up secure voice channel</p>
              </>
            )}

            {isOnCall && (
              <>
                <div className="relative w-14 h-14 rounded-full bg-green-600 flex items-center justify-center mb-3 shadow-lg shadow-green-900">
                  <span className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-30" />
                  <PhoneCall size={24} className="text-white relative z-10" />
                </div>
                <p className="text-green-400 text-3xl font-bold tabular-nums">{fmt(duration)}</p>
                <p className={`text-gray-300 text-sm mt-1 ${language !== 'en' ? 'font-hindi' : ''}`}>
                  {language === 'hi' ? 'बोलिए — सुन रही हूँ' :
                   language === 'mr' ? 'बोला — ऐकत आहे' :
                   language === 'ta' ? 'பேசுங்கள் — கேட்கிறேன்' :
                   "Speak — I'm listening"}
                </p>
              </>
            )}

            {callStatus === 'error' && (
              <>
                <div className="w-14 h-14 rounded-full bg-red-700 flex items-center justify-center mb-3">
                  <PhoneOff size={24} className="text-white" />
                </div>
                {error === 'daily_limit_exceeded' ? (
                  <>
                    <p className="text-red-400 text-sm font-medium text-center px-2">Daily call limit reached</p>
                    <p className="text-gray-500 text-xs mt-1 px-2">3 sessions used · Resets midnight UTC</p>
                  </>
                ) : (
                  <>
                    <p className="text-red-400 text-sm font-medium text-center px-2">{error || 'Connection failed'}</p>
                    <button onClick={() => setCallStatus('idle')} className="text-amber-400 text-xs mt-1 hover:text-amber-300">
                      Try again
                    </button>
                  </>
                )}
              </>
            )}
          </div>

          {/* DTMF digit display */}
          <div className="min-h-[28px] text-center mb-1">
            {isOnCall && dtmfDisplay && (
              <div className="flex items-center justify-center gap-2">
                <span className="text-white text-xl font-mono tracking-widest">{dtmfDisplay}</span>
                <button onClick={() => setDtmfDisplay('')} className="text-gray-500 hover:text-gray-300 transition-colors">
                  <Delete size={14} />
                </button>
              </div>
            )}
            {isOnCall && !dtmfDisplay && (
              <p className="text-gray-600 text-xs">Use keypad if prompted for input</p>
            )}
          </div>

          {/* ── Quota meter (always visible on screen) ── */}
          <div className="mt-3 px-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-gray-600 text-[10px]">Daily allowance</span>
              <span className={`text-[10px] font-mono ${quotaPercent >= 80 ? 'text-red-400' : quotaPercent >= 50 ? 'text-amber-400' : 'text-gray-500'}`}>
                {fmt(quotaRemaining)} left
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-800 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ${
                  quotaPercent >= 80 ? 'bg-red-500' :
                  quotaPercent >= 50 ? 'bg-amber-400' :
                  'bg-green-500'
                }`}
                style={{ width: `${100 - quotaPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* ── Keypad ── */}
        <div className="px-5 pt-4 pb-3" style={{ background: '#16162a' }}>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {KEYPAD_KEYS.map(k => (
              <DialerKey key={k.digit} digit={k.digit} sub={k.sub} onPress={pressKey} active={isOnCall} />
            ))}
          </div>

          {/* ── Action Row ── */}
          <div className="flex items-center justify-between px-2 pb-4 mt-1">
            {/* Mute */}
            <button
              onClick={toggleMute}
              disabled={!isOnCall}
              className={`w-14 h-14 rounded-full flex items-center justify-center transition-all disabled:opacity-30 ${
                isMuted ? 'bg-red-600 text-white shadow-lg shadow-red-900' : 'bg-[#2a2a3a] text-gray-300 hover:bg-[#383850]'
              }`}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <MicOff size={22} /> : <Mic size={22} />}
            </button>

            {/* Main call / end button */}
            {isOnCall ? (
              <button
                onClick={endCall}
                className="w-20 h-20 rounded-full bg-red-600 hover:bg-red-500 text-white flex items-center justify-center shadow-2xl shadow-red-900 transition-all active:scale-95 hover:scale-105"
              >
                <PhoneOff size={32} />
              </button>
            ) : (
              <button
                onClick={startCall}
                disabled={isConnecting || quotaExhausted}
                className={`w-20 h-20 rounded-full flex items-center justify-center shadow-2xl transition-all active:scale-95 ${
                  isConnecting
                    ? 'bg-amber-500 text-white cursor-wait shadow-amber-900'
                    : 'bg-green-600 hover:bg-green-500 text-white shadow-green-900 hover:scale-105'
                }`}
              >
                {isConnecting ? <Loader2 size={32} className="animate-spin" /> : <Phone size={32} />}
              </button>
            )}

            {/* Switch to text */}
            <button
              onClick={() => setShowText(true)}
              disabled={isOnCall}
              className="w-14 h-14 rounded-full bg-[#2a2a3a] text-gray-300 hover:bg-[#383850] flex items-center justify-center transition-all disabled:opacity-30"
              title="Switch to text"
            >
              <Keyboard size={20} />
            </button>
          </div>
        </div>
      </div>
      )}

      {/* Tips below phone */}
      {callStatus === 'idle' && !quotaExhausted && (
        <p className="text-xs text-content-tertiary mt-5 text-center max-w-xs">
          Tap the green button to start · Free 10 min / day · No sign-up needed
        </p>
      )}
      {isOnCall && (
        <p className="text-xs text-gray-500 mt-4 text-center max-w-xs">
          🎙️ Keypad sends DTMF tones · Call auto-ends when daily limit is reached
        </p>
      )}
      {quotaExhausted && (
        <button
          onClick={() => {
            // Hard reset for demo / testing — remove in production if desired
            saveQuota(0); setQuotaUsed(0)
          }}
          className="mt-3 text-[10px] text-gray-400 hover:text-gray-300 underline"
        >
          Reset demo quota
        </button>
      )}
    </div>
  )
}



// ══════════════════════════════════════════════════════
//  MAIN TRY PAGE
// ══════════════════════════════════════════════════════
export default function TryPage() {
  const [tab, setTab] = useState('voice') // 'voice' | 'callback'

  return (
    <div className="min-h-screen bg-surface-secondary pt-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 md:px-12 py-10">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-accent-500 transition-colors mb-6">
            <ArrowLeft size={16} />
            Back to Home
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold text-content-primary mb-2">
            Try VaaniSeva
          </h1>
          <p className="text-lg text-content-secondary">
            Talk to VaaniSeva — speak directly from your browser or get a callback on your phone
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-4xl mx-auto px-6 md:px-12 mt-8">
        <div className="flex bg-white rounded-2xl border border-gray-100 p-1.5 shadow-sm max-w-lg">
          <button
            onClick={() => setTab('voice')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
              tab === 'voice' ? 'bg-gradient-accent text-white shadow-sm' : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <Phone size={16} />
            Live Call
          </button>
          <button
            onClick={() => setTab('callback')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
              tab === 'callback' ? 'bg-gradient-accent text-white shadow-sm' : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <Phone size={16} />
            Call Me Back
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-4xl mx-auto px-6 md:px-12 py-4 md:py-8">
        <div className={`bg-white rounded-2xl border border-gray-100 shadow-sm overflow-y-auto ${tab === 'voice' ? 'p-4 md:p-8' : 'p-8 md:p-12'}`}>
          {tab === 'voice' ? <VoiceChat /> : <CallMeBack />}
        </div>
      </div>
    </div>
  )
}
