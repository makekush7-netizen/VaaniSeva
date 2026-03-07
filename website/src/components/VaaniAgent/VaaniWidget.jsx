import React, { useState, useRef, useEffect, Suspense, useCallback } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useNavigate } from 'react-router-dom'
import AvatarModel from './AvatarModel'
import './styles.css'

// ── Error Boundary ────────────────────────────────────
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false } }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(err) { console.error('[Vaani Avatar Error]', err) }
  render() { return this.state.hasError ? null : this.props.children }
}

// ── Action Executor ───────────────────────────────────
const executeAction = (action, navigate) => {
  const { type, target, value } = action
  switch (type) {
    case 'navigate':
      setTimeout(() => navigate(target), 1500)
      break
    case 'scroll':
      const el = document.querySelector(target)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      break
    case 'highlight':
      const hl = document.querySelector(target)
      if (hl) {
        hl.style.transition = 'all 0.3s ease'
        hl.style.boxShadow = '0 0 20px 5px rgba(255, 107, 0, 0.5)'
        hl.style.outline = '3px solid #FF6B00'
        setTimeout(() => { hl.style.boxShadow = ''; hl.style.outline = '' }, 3000)
      }
      break
    default:
      break
  }
}

// ── Main Widget ───────────────────────────────────────
export default function VaaniWidget({ apiBaseUrl } = {}) {
  const base = apiBaseUrl || import.meta.env.VITE_API_BASE || 'http://localhost:8000'
  const navigate = useNavigate()

  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState('agent')   // 'agent' | 'text'
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'नमस्ते! मैं वाणी हूँ। आप किस सरकारी योजना के बारे में जानना चाहते हैं?' }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [currentResponse, setCurrentResponse] = useState('')
  const [pendingActions, setPendingActions] = useState([])

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)
  const sessionIdRef = useRef(crypto.randomUUID())

  // ── Load chat history ─────────────────────────────
  useEffect(() => {
    const saved = localStorage.getItem('vaani_chat_history')
    if (saved) { try { setMessages(JSON.parse(saved)) } catch (_) {} }
  }, [])

  // ── Save chat history ─────────────────────────────
  useEffect(() => {
    if (messages.length <= 1) return
    localStorage.setItem('vaani_chat_history', JSON.stringify(messages))
  }, [messages])

  // ── Scroll to bottom ──────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Speech Recognition (Hindi-first) ──────────────
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SR()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'hi-IN'   // Hindi-first
      recognitionRef.current.onresult = (event) => {
        setInput(Array.from(event.results).map((r) => r[0].transcript).join(''))
      }
      recognitionRef.current.onend = () => setIsRecording(false)
    }
  }, [])

  // ── Execute pending actions ───────────────────────
  useEffect(() => {
    if (pendingActions.length > 0 && !currentResponse) {
      pendingActions.forEach((action, i) => {
        setTimeout(() => executeAction(action, navigate), i * 500)
      })
      setPendingActions([])
    }
  }, [currentResponse, pendingActions, navigate])

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop()
      setIsRecording(false)
    } else {
      recognitionRef.current?.start()
      setIsRecording(true)
    }
  }

  // ── Send message ──────────────────────────────────
  const handleSend = async () => {
    if (!input.trim()) return
    const userMsg = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setIsTyping(true)

    window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'thinking' }))

    try {
      const res = await fetch(`${base}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg, language: 'hi', session_id: sessionIdRef.current })
      })
      const data = await res.json()

      let finalText = data.answer || 'Sorry, something went wrong.'

      // Parse emotion tag
      const emotionMatch = finalText.match(/\[EMOTION:\s*(\w+)\]/i)
      if (emotionMatch) {
        const emotion = emotionMatch[1].toLowerCase()
        const animMap = {
          happy: 'mainidle', laugh: 'laughing', thinking: 'thinking',
          thankful: 'thankful', bashful: 'bashful', waving: 'waveing', wave: 'waveing'
        }
        window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: animMap[emotion] || 'mainidle' }))
        finalText = finalText.replace(emotionMatch[0], '').trim()
      } else {
        window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'mainidle' }))
      }

      // Parse action tag
      if (data.data?.actions?.length > 0) {
        setPendingActions(data.data.actions)
      }

      // Clean text for TTS (remove emojis, brackets)
      const cleanTTS = finalText
        .replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '')
        .replace(/\(.*?\)/g, '').replace(/\[.*?\]/g, '').trim()

      if (cleanTTS.length > 0) {
        speakResponse(cleanTTS, finalText, data.audio_url)
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: finalText || '😊' }])
        setIsTyping(false)
      }
    } catch (e) {
      console.error('[Vaani Error]', e)
      setIsTyping(false)
      window.dispatchEvent(new CustomEvent('aura:setAnimation', { detail: 'mainidle' }))
      setMessages((prev) => [...prev, { role: 'assistant', content: 'कनेक्शन में समस्या है। कृपया दोबारा कोशिश करें।' }])
    }
  }

  // ── TTS + Lip Sync Pipeline ───────────────────────
  const speakResponse = async (text, displayText, audioUrl) => {
    setIsTyping(false)
    try {
      if (!audioUrl) throw new Error('No audio URL')
      const res = await fetch(audioUrl)

      if (res.ok) {
        const arrayBuffer = await res.arrayBuffer()
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

        const source = audioContext.createBufferSource()
        source.buffer = audioBuffer
        const analyser = audioContext.createAnalyser()
        analyser.fftSize = 2048
        const dataArray = new Uint8Array(analyser.frequencyBinCount)

        source.connect(analyser)
        analyser.connect(audioContext.destination)
        source.start()

        // Word-by-word subtitle sync
        const duration = audioBuffer.duration * 1000
        const words = text.split(' ')
        const timePerWord = duration / words.length
        let current = ''
        setCurrentResponse('')

        words.forEach((word, i) => {
          setTimeout(() => {
            current += (i === 0 ? '' : ' ') + word
            setCurrentResponse(current)
            if (i === words.length - 1) {
              setMessages((prev) => [...prev, { role: 'assistant', content: displayText || text }])
            }
          }, i * timePerWord)
        })

        // Lip sync — read audio amplitude → drive mouthOpen morph
        let rafId
        const updateMouth = () => {
          analyser.getByteTimeDomainData(dataArray)
          let sum = 0
          for (let i = 0; i < dataArray.length; i++) {
            sum += Math.pow((dataArray[i] - 128) / 128, 2)
          }
          const volume = Math.min(1, Math.sqrt(sum / dataArray.length) * 4)
          window.dispatchEvent(new CustomEvent('aura:setMorph', { detail: { name: 'mouthOpen', value: volume } }))
          rafId = requestAnimationFrame(updateMouth)
        }
        updateMouth()

        source.onended = () => {
          cancelAnimationFrame(rafId)
          window.dispatchEvent(new CustomEvent('aura:setMorph', { detail: { name: 'mouthOpen', value: 0 } }))
          audioContext.close()
          setTimeout(() => setCurrentResponse(''), 3000)
        }
      } else {
        throw new Error('TTS failed')
      }
    } catch (e) {
      console.error('[TTS Error]', e)
      // Fallback: just show text
      setMessages((prev) => [...prev, { role: 'assistant', content: displayText || text }])
      setCurrentResponse(text)
      setTimeout(() => setCurrentResponse(''), 3000)
    }
  }

  const clearHistory = () => {
    setMessages([{ role: 'assistant', content: 'नमस्ते! मैं वाणी हूँ। आप किस सरकारी योजना के बारे में जानना चाहते हैं?' }])
    localStorage.removeItem('vaani_chat_history')
  }

  // ── Quick action chips ────────────────────────────
  const quickChips = [
    'PM Kisan क्या है?',
    'आयुष्मान भारत',
    'नरेगा जॉब कार्ड',
    'Help in English',
  ]

  // ── Render ────────────────────────────────────────
  return (
    <div className="vaani-widget-container">
      {!isOpen ? (
        /* ── Floating Button ─── */
        <div className="vaani-floating-btn" onClick={() => setIsOpen(true)}>
          <div className="vaani-avatar-preview">
            <Canvas
              camera={{ position: [0, 1.64, 0.5], fov: 20 }}
              onCreated={({ camera }) => camera.lookAt(0.05, 1.63, 0)}
            >
              <ambientLight intensity={1} />
              <directionalLight position={[2, 2, 2]} />
              <ErrorBoundary>
                <Suspense fallback={null}>
                  <AvatarModel modelUrl="/models/vaani.glb" mini={true} showWaistUp />
                </Suspense>
              </ErrorBoundary>
            </Canvas>
          </div>
          <div className="vaani-online-dot"></div>
          <div className="vaani-avatar-badge">वाणी AI</div>
          <div className="vaani-pulse"></div>
        </div>
      ) : (
        /* ── Chat Window ─── */
        <div className="vaani-chat-window">
          {/* Header */}
          <div className="vaani-header">
            <div className="vaani-header-title">
              <span className="vaani-status-dot"></span>
              <span className="font-hindi">वाणी</span> AI
            </div>
            <div className="vaani-header-controls">
              <button onClick={clearHistory} title="Clear">🗑️</button>
              <button onClick={() => setIsOpen(false)} title="Minimize">✕</button>
            </div>
          </div>

          {/* Mode Tabs */}
          <div className="vaani-mode-tabs">
            <button className={mode === 'agent' ? 'active' : ''} onClick={() => setMode('agent')}>🤖 3D Agent</button>
            <button className={mode === 'text' ? 'active' : ''} onClick={() => setMode('text')}>💬 Chat</button>
          </div>

          {/* Content */}
          <div className="vaani-content">
            {mode === 'agent' ? (
              <div className="vaani-3d-view">
                <Canvas camera={{ position: [0, 1.55, 1.2], fov: 28 }}>
                  <ambientLight intensity={0.9} />
                  <directionalLight position={[3, 3, 3]} />
                  <OrbitControls
                    target={[0, 1.52, 0]}
                    enableZoom={false}
                    enablePan={false}
                    minPolarAngle={Math.PI / 2.5}
                    maxPolarAngle={Math.PI / 1.8}
                    minAzimuthAngle={-Math.PI / 6}
                    maxAzimuthAngle={Math.PI / 6}
                  />
                  <ErrorBoundary>
                    <Suspense fallback={null}>
                      <AvatarModel modelUrl="/models/vaani.glb" showWaistUp />
                    </Suspense>
                  </ErrorBoundary>
                </Canvas>
                {currentResponse && <div className="vaani-subs">{currentResponse}</div>}
                {isTyping && (
                  <div className="vaani-thinking">
                    <span>सोच रही हूँ</span>
                    <span className="dots">...</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="vaani-chat-list">
                {messages.map((m, i) => (
                  <div key={i} className={`msg ${m.role}`}>{m.content}</div>
                ))}
                {isTyping && (
                  <div className="msg assistant typing">
                    <span className="typing-indicator"><span></span><span></span><span></span></span>
                  </div>
                )}
                <div ref={messagesEndRef}></div>
              </div>
            )}
          </div>

          {/* Quick Chips */}
          <div className="vaani-chips">
            {quickChips.map((chip) => (
              <button
                key={chip}
                onClick={() => { setInput(chip); setTimeout(() => handleSend(), 100) }}
                className="vaani-chip"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="vaani-input-row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="कुछ भी पूछें... Ask anything..."
              disabled={isTyping}
            />
            <button onClick={toggleRecording} className={isRecording ? 'recording' : ''} title="Voice">
              🎤
            </button>
            <button onClick={handleSend} disabled={isTyping || !input.trim()} title="Send">
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
