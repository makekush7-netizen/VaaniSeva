import React, { useState, useRef, useEffect } from 'react'
import { Phone, PhoneCall, PhoneOff, Mic, MicOff, Loader2, ArrowLeft, Globe } from 'lucide-react'
import { Link } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const TWILIO_PHONE = import.meta.env.VITE_TWILIO_PHONE || '+12602048966'

// ══════════════════════════════════════════════════════
//  TAB 1: Call from Browser (Twilio Client JS SDK)
// ══════════════════════════════════════════════════════
function BrowserCall() {
  const [status, setStatus] = useState('idle') // idle | connecting | connected | ended | error
  const [duration, setDuration] = useState(0)
  const [isMuted, setIsMuted] = useState(false)
  const deviceRef = useRef(null)
  const callRef = useRef(null)
  const timerRef = useRef(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (callRef.current) callRef.current.disconnect()
    }
  }, [])

  const startCall = async () => {
    setStatus('connecting')
    try {
      // 1. Get capability token from our backend
      const res = await fetch(`${API_BASE}/web/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })

      if (!res.ok) throw new Error('Failed to get token')
      const { token } = await res.json()

      // 2. Initialize Twilio Device
      const { Device } = await import('@twilio/voice-sdk')
      const device = new Device(token, {
        codecPreferences: ['opus', 'pcmu'],
        enableRingingState: true,
      })
      deviceRef.current = device

      // 3. Place the call
      const call = await device.connect({
        params: { To: TWILIO_PHONE }
      })
      callRef.current = call

      call.on('accept', () => {
        setStatus('connected')
        setDuration(0)
        timerRef.current = setInterval(() => {
          setDuration((d) => d + 1)
        }, 1000)
      })

      call.on('disconnect', () => {
        setStatus('ended')
        if (timerRef.current) clearInterval(timerRef.current)
      })

      call.on('error', (err) => {
        console.error('[Twilio Error]', err)
        setStatus('error')
        if (timerRef.current) clearInterval(timerRef.current)
      })

    } catch (err) {
      console.error('[Call Error]', err)
      setStatus('error')
    }
  }

  const endCall = () => {
    if (callRef.current) callRef.current.disconnect()
    setStatus('ended')
    if (timerRef.current) clearInterval(timerRef.current)
  }

  const toggleMute = () => {
    if (callRef.current) {
      callRef.current.mute(!isMuted)
      setIsMuted(!isMuted)
    }
  }

  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center">
      {/* Status Display */}
      <div className="w-full max-w-md mx-auto text-center">

        {/* Call Circle */}
        <div className="relative mx-auto w-48 h-48 mb-8">
          {/* Pulse rings during connecting/connected */}
          {(status === 'connecting' || status === 'connected') && (
            <>
              <div className="absolute inset-0 rounded-full bg-saffron-500/10 animate-ping" style={{ animationDuration: '2s' }} />
              <div className="absolute inset-4 rounded-full bg-saffron-500/10 animate-ping" style={{ animationDuration: '2s', animationDelay: '0.5s' }} />
            </>
          )}

          <div className={`relative w-48 h-48 rounded-full flex flex-col items-center justify-center transition-all duration-500 ${
            status === 'connected'
              ? 'bg-green-50 border-4 border-green-400'
              : status === 'connecting'
                ? 'bg-saffron-50 border-4 border-saffron-300'
                : status === 'error'
                  ? 'bg-red-50 border-4 border-red-300'
                  : 'bg-gray-50 border-4 border-gray-200'
          }`}>
            {status === 'connecting' ? (
              <Loader2 size={40} className="text-saffron-500 animate-spin" />
            ) : status === 'connected' ? (
              <>
                <PhoneCall size={36} className="text-green-500 mb-2" />
                <span className="text-2xl font-mono font-bold text-green-600">{formatTime(duration)}</span>
              </>
            ) : status === 'error' ? (
              <Phone size={36} className="text-red-400" />
            ) : (
              <Phone size={40} className="text-gray-400" />
            )}
          </div>
        </div>

        {/* Status Text */}
        <p className="text-lg font-semibold text-content-primary mb-1">
          {status === 'idle' && 'Ready to Call'}
          {status === 'connecting' && 'Connecting to VaaniSeva...'}
          {status === 'connected' && 'Connected — Speak Now'}
          {status === 'ended' && 'Call Ended'}
          {status === 'error' && 'Connection Failed'}
        </p>
        <p className="text-sm text-content-secondary mb-8">
          {status === 'idle' && 'Call VaaniSeva directly from your browser using your microphone'}
          {status === 'connecting' && 'Setting up secure connection...'}
          {status === 'connected' && 'Ask about any government scheme in Hindi or English'}
          {status === 'ended' && 'Thank you for trying VaaniSeva!'}
          {status === 'error' && 'Please check your microphone permissions and try again'}
        </p>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4">
          {status === 'idle' || status === 'ended' || status === 'error' ? (
            <button onClick={startCall} className="btn-primary text-base px-10 py-4">
              <Phone size={20} />
              {status === 'ended' ? 'Call Again' : 'Start Call'}
            </button>
          ) : status === 'connected' ? (
            <>
              <button
                onClick={toggleMute}
                className={`w-14 h-14 rounded-full flex items-center justify-center transition-colors ${
                  isMuted ? 'bg-red-100 text-red-500' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {isMuted ? <MicOff size={22} /> : <Mic size={22} />}
              </button>
              <button
                onClick={endCall}
                className="w-14 h-14 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors"
              >
                <PhoneOff size={22} />
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2 text-content-secondary">
              <Loader2 size={18} className="animate-spin" />
              <span className="text-sm">Please wait...</span>
            </div>
          )}
        </div>

        {/* Trial notice */}
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-xl text-left">
          <p className="text-xs text-amber-700">
            <strong>Note:</strong> We're currently on a Twilio trial account. You may hear a brief trial message before connecting.
            For the best experience, call us directly at <strong>+1 260 204 8966</strong> from your phone.
          </p>
        </div>
      </div>
    </div>
  )
}

// ══════════════════════════════════════════════════════
//  TAB 2: Request Callback
// ══════════════════════════════════════════════════════
function CallbackRequest() {
  const [phone, setPhone] = useState('')
  const [lang, setLang] = useState('hi')
  const [status, setStatus] = useState('idle') // idle | sending | success | error
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!phone.trim()) return

    // Basic validation
    const cleanPhone = phone.replace(/\s+/g, '')
    if (cleanPhone.length < 10) {
      setErrorMsg('Please enter a valid phone number')
      return
    }

    setStatus('sending')
    setErrorMsg('')

    try {
      const res = await fetch(`${API_BASE}/web/callback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: cleanPhone.startsWith('+') ? cleanPhone : `+91${cleanPhone}`,
          lang
        })
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.error || 'Failed to initiate callback')
      }

      setStatus('success')
    } catch (err) {
      console.error('[Callback Error]', err)
      setStatus('error')
      setErrorMsg(err.message || 'Something went wrong. Please try again.')
    }
  }

  if (status === 'success') {
    return (
      <div className="text-center py-12">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <PhoneCall size={36} className="text-green-500" />
        </div>
        <h3 className="text-xl font-bold text-content-primary mb-2">Calling You Now!</h3>
        <p className="text-content-secondary mb-2">
          VaaniSeva is dialing your number. Please pick up the call.
        </p>
        <p className="font-hindi text-saffron-600 text-sm mb-8">
          आपके नंबर पर कॉल आ रही है। कृपया कॉल उठाएं।
        </p>
        <button
          onClick={() => { setStatus('idle'); setPhone('') }}
          className="btn-secondary"
        >
          Request Another Call
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Phone Number */}
        <div>
          <label className="block text-sm font-medium text-content-primary mb-2">
            Phone Number <span className="font-hindi text-content-secondary">— फ़ोन नंबर</span>
          </label>
          <div className="flex gap-2">
            <div className="flex items-center bg-gray-50 border border-gray-200 rounded-xl px-4 text-sm text-content-secondary font-mono">
              +91
            </div>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="98765 43210"
              className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-content-primary bg-white focus:border-saffron-500 focus:ring-1 focus:ring-saffron-500 outline-none transition-colors font-mono text-lg"
              maxLength={15}
            />
          </div>
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-content-primary mb-3">
            Preferred Language <span className="font-hindi text-content-secondary">— भाषा चुनें</span>
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setLang('hi')}
              className={`px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                lang === 'hi'
                  ? 'border-saffron-500 bg-saffron-50 text-saffron-700'
                  : 'border-gray-200 bg-white text-content-secondary hover:border-gray-300'
              }`}
            >
              <span className="font-hindi text-base">हिंदी</span>
              <span className="block text-xs mt-0.5 opacity-70">Hindi</span>
            </button>
            <button
              type="button"
              onClick={() => setLang('en')}
              className={`px-4 py-3 rounded-xl border-2 text-sm font-medium transition-all ${
                lang === 'en'
                  ? 'border-saffron-500 bg-saffron-50 text-saffron-700'
                  : 'border-gray-200 bg-white text-content-secondary hover:border-gray-300'
              }`}
            >
              <span className="text-base">English</span>
              <span className="block text-xs mt-0.5 opacity-70">अंग्रेज़ी</span>
            </button>
          </div>
        </div>

        {/* Error */}
        {(status === 'error' || errorMsg) && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl">
            <p className="text-sm text-red-600">{errorMsg || 'Something went wrong. Please try again.'}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={status === 'sending' || !phone.trim()}
          className="btn-primary w-full text-base py-4 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {status === 'sending' ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Calling...
            </>
          ) : (
            <>
              <Phone size={18} />
              Call Me Now
            </>
          )}
        </button>

        {/* Trial notice */}
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <p className="text-xs text-amber-700">
            <strong>Note:</strong> Our Twilio account is being upgraded. Currently, callbacks work only to verified phone numbers.
            For immediate access, call us directly at <strong>+1 260 204 8966</strong>.
          </p>
        </div>
      </form>
    </div>
  )
}

// ══════════════════════════════════════════════════════
//  MAIN TRY PAGE
// ══════════════════════════════════════════════════════
export default function TryPage() {
  const [tab, setTab] = useState('browser') // 'browser' | 'callback'

  return (
    <div className="min-h-screen bg-surface-secondary pt-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-6 md:px-12 py-10">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-saffron-500 transition-colors mb-6">
            <ArrowLeft size={16} />
            Back to Home
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold text-content-primary mb-2">
            <span className="font-hindi">वाणीसेवा आज़माएं</span>
          </h1>
          <p className="text-lg text-content-secondary">
            Try VaaniSeva — call directly from your browser or request a callback
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-4xl mx-auto px-6 md:px-12 mt-8">
        <div className="flex bg-white rounded-2xl border border-gray-100 p-1.5 shadow-sm max-w-md">
          <button
            onClick={() => setTab('browser')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
              tab === 'browser'
                ? 'bg-gradient-saffron text-white shadow-sm'
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <Globe size={16} />
            Call from Browser
          </button>
          <button
            onClick={() => setTab('callback')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold transition-all ${
              tab === 'callback'
                ? 'bg-gradient-saffron text-white shadow-sm'
                : 'text-content-secondary hover:text-content-primary'
            }`}
          >
            <Phone size={16} />
            Request Callback
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-4xl mx-auto px-6 md:px-12 py-10">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 md:p-12">
          {tab === 'browser' ? <BrowserCall /> : <CallbackRequest />}
        </div>
      </div>
    </div>
  )
}
