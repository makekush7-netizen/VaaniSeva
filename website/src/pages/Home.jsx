import React, { useRef, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Phone, ArrowRight, Mic, MessageCircle, X } from 'lucide-react'
import {
  PMKisanIcon, AyushmanIcon, MGNREGAIcon, PMAwasIcon, SukanyaIcon,
  UjjwalaIcon, JanDhanIcon, MudraIcon, AtalPensionIcon, FasalBimaIcon,
  MentalHealthIcon, MandiIcon,
  ShieldStarIcon, ClockRoundIcon, MultiLanguageIcon, IndiaPeopleIcon,
  PhoneWavesIcon, MicSpeakIcon,
} from '../components/icons/VaaniIcons'
import { CallMeBack } from './TryPage'

const TICKER_TEXT =
  'हिंदी में उपलब्ध  ·  मराठीत उपलब्ध  ·  தமிழில் கிடைக்கும்  ·  Available in English  ·  తెలుగులో అందుబాటులో  ·  ಕನ್ನಡದಲ್ಲಿ ಲಭ್ಯವಿದೆ  ·  বাংলায় পাওয়া যাচ্ছে  ·'

const schemes = [
  { name: 'PM-Kisan',            hindi: 'पीएम किसान',          desc: 'Direct income support of ₹6,000/year to farmer families',                   icon: <PMKisanIcon size={24} />      },
  { name: 'Ayushman Bharat',     hindi: 'आयुष्मान भारत',       desc: 'Free health coverage up to ₹5 lakh per family per year',                    icon: <AyushmanIcon size={24} />     },
  { name: 'MGNREGA',             hindi: 'मनरेगा',              desc: '100 days guaranteed employment for rural households',                        icon: <MGNREGAIcon size={24} />      },
  { name: 'PM Awas Yojana',      hindi: 'पीएम आवास योजना',     desc: 'Affordable housing for economically weaker sections',                       icon: <PMAwasIcon size={24} />       },
  { name: 'Sukanya Samriddhi',   hindi: 'सुकन्या समृद्धि',     desc: 'Savings scheme for girl child education and marriage',                      icon: <SukanyaIcon size={24} />      },
  { name: 'PM Ujjwala',          hindi: 'पीएम उज्ज्वला',       desc: 'Free LPG connections for BPL households',                                   icon: <UjjwalaIcon size={24} />      },
  { name: 'Jan Dhan Yojana',     hindi: 'जन धन योजना',         desc: 'Zero-balance bank accounts with insurance cover',                           icon: <JanDhanIcon size={24} />      },
  { name: 'PM Mudra Yojana',     hindi: 'पीएम मुद्रा योजना',    desc: 'Collateral-free loans up to ₹10 lakh for small businesses',                icon: <MudraIcon size={24} />        },
  { name: 'Atal Pension',        hindi: 'अटल पेंशन योजना',     desc: 'Guaranteed pension of ₹1,000-5,000/month after 60',                        icon: <AtalPensionIcon size={24} />  },
  { name: 'Fasal Bima Yojana',   hindi: 'फसल बीमा योजना',      desc: 'Crop insurance protection for farmers against natural disasters',           icon: <FasalBimaIcon size={24} />    },
  { name: 'iCall Mental Health', hindi: 'मानसिक स्वास्थ्य',    desc: 'Free counselling helpline — speak to someone who listens',                  icon: <MentalHealthIcon size={24} /> },
  { name: 'Mandi Prices Live',   hindi: 'मंडी भाव',            desc: 'Live crop market prices from 3,000+ mandis across India, updated daily',   icon: <MandiIcon size={24} />        },
]

const steps = [
  { num: '01', title: 'Call from Any Phone',    desc: 'Dial from a basic keypad phone, smartphone, or anything in between. No app, no data, no setup.',        icon: PhoneWavesIcon },
  { num: '02', title: 'Speak in Your Language', desc: 'Hindi, Marathi, Tamil, English — speak naturally in your own words and dialect.',                        icon: MicSpeakIcon   },
  { num: '03', title: 'Get Verified Answers',   desc: 'AI answers in under 4 seconds. Every fact is verified by human experts before it reaches you.',          icon: MessageCircle  },
]

const stats = [
  { value: '30+',   label: 'Government Schemes',     icon: ShieldStarIcon      },
  { value: '24/7',  label: 'Always Available',        icon: ClockRoundIcon      },
  { value: '4',     label: 'Languages Supported',     icon: MultiLanguageIcon   },
  { value: '500M+', label: 'Indians We Aim to Serve', icon: IndiaPeopleIcon     },
]

export default function Home() {
  const videoRef = useRef(null)
  const [showCallWidget, setShowCallWidget] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)')
    const handle = (e) => {
      if (!videoRef.current) return
      if (e.matches) { videoRef.current.pause() }
      else { videoRef.current.play().catch(() => {}) }
    }
    handle(mq)
    mq.addEventListener('change', handle)
    return () => mq.removeEventListener('change', handle)
  }, [])

  return (
    <>
      {/* === HERO === */}
      <section className="relative w-full overflow-hidden" style={{ minHeight: '100vh' }}>

        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          src="/hero.mp4"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          aria-hidden="true"
        />

        {/* Left gradient: warm cinematic — right side breathes */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'linear-gradient(to right, rgba(15,15,15,0.82) 0%, rgba(0,0,0,0.05) 48%)',
          }}
        />

        <div className="relative z-10 flex items-center" style={{ minHeight: '100vh' }}>
          <div className="w-full max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-24">
            <div className="w-full md:w-[52%] lg:w-[46%]">

              {/* Pill badge */}
              <div className="inline-flex items-center gap-2 bg-black/40 backdrop-blur-sm border border-white/15 rounded-full px-4 py-1.5 mb-7">
                <span className="w-2 h-2 rounded-full animate-live-dot flex-shrink-0" style={{ backgroundColor: '#F0A832' }} />
                <span className="text-white/85 text-sm font-medium tracking-wide">Live Now — Call Anytime</span>
              </div>

              {/* Main headline */}
              <h1
                className="font-extrabold text-white leading-tight tracking-tight mb-4"
                style={{ fontSize: 'clamp(2.2rem, 5vw, 4rem)' }}
              >
                India&apos;s Knowledge
                <br />
                <span style={{ color: '#F0A832' }}>Now in Every Voice</span>
              </h1>

              {/* Subheadline */}
              <p
                className="text-base md:text-lg font-medium leading-relaxed mb-6"
                style={{ color: 'rgba(255,255,255,0.72)' }}
              >
                Hundreds of millions of Indians have no smartphone, no internet, no access to digital services.
                <br />
                VaaniSeva changes that — one voice call at a time.
              </p>

              {/* Language ticker */}
              <div
                className="overflow-hidden rounded-lg mb-6"
                style={{
                  background: 'rgba(212,134,11,0.15)',
                  border: '1px solid rgba(212,134,11,0.25)',
                  backdropFilter: 'blur(6px)',
                  padding: '7px 0',
                }}
              >
                <div
                  className="flex whitespace-nowrap font-hindi"
                  style={{ animation: 'tickerScroll 28s linear infinite', width: 'max-content' }}
                >
                  {[TICKER_TEXT, TICKER_TEXT].map((txt, i) => (
                    <span
                      key={i}
                      className="text-xs font-medium"
                      style={{ color: '#F0A832', padding: '0 2.5rem', minWidth: 'max-content' }}
                    >
                      {txt}
                    </span>
                  ))}
                </div>
              </div>

              {/* Trust badges */}
              <div className="flex flex-wrap gap-x-5 gap-y-2 mb-8">
                {[
                  { icon: '📞', text: 'Works on ₹500 phones' },
                  { icon: '🚫', text: 'No internet needed'    },
                  { icon: '⚡', text: 'Answer in 4 sec'       },
                ].map(({ icon, text }) => (
                  <div key={text} className="flex items-center gap-1.5 text-sm font-medium" style={{ color: 'rgba(255,255,255,0.78)' }}>
                    <span>{icon}</span>
                    <span>{text}</span>
                  </div>
                ))}
              </div>

              {/* CTAs */}
              <div className="flex flex-wrap items-center gap-3 mb-5">
                <a
                  href="tel:+19788309619"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-bold text-white text-[15px] active:scale-[0.98] transition-all duration-200"
                  style={{ background: '#D4860B', boxShadow: '0 4px 20px rgba(212,134,11,0.40)' }}
                >
                  <Phone size={17} />
                  Call Now — +1 978 830 9619
                </a>
                <Link
                  to="/try"
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-bold text-white text-[15px] active:scale-[0.98] transition-all duration-200 backdrop-blur-sm hover:bg-white/10"
                  style={{ border: '2px solid rgba(255,255,255,0.38)' }}
                >
                  Try on Web
                  <ArrowRight size={16} />
                </Link>
              </div>

              <p className="text-xs" style={{ color: 'rgba(255,255,255,0.32)' }}>
                No smartphone needed &nbsp;·&nbsp; No internet required &nbsp;·&nbsp; Works on ₹500 phones
              </p>

            </div>
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce z-10">
          <div className="w-6 h-10 border-2 border-white/25 rounded-full flex justify-center pt-2">
            <div className="w-1 h-2.5 bg-white/40 rounded-full" />
          </div>
        </div>
      </section>

      {/* === STATS === */}
      <section className="bg-surface-secondary border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-accent-50 rounded-xl flex items-center justify-center flex-shrink-0">
                  <s.icon size={20} className="text-accent-500" />
                </div>
                <div>
                  <p className="text-xl font-bold text-content-primary">{s.value}</p>
                  <p className="text-xs text-content-tertiary">{s.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* === HOW IT WORKS === */}
      <section id="how-it-works" className="section bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-accent-500 uppercase tracking-wider mb-2">Simple Process</p>
            <h2 className="section-title text-center">How It Works</h2>
            <p className="section-subtitle mx-auto mt-2">Three steps. No app downloads. No internet required.</p>
          </div>
          <div className="relative grid md:grid-cols-3 gap-8">
            <div
              className="hidden md:block absolute"
              style={{
                top: '72px',
                left: 'calc(16.67% + 2rem)',
                right: 'calc(16.67% + 2rem)',
                height: '2px',
                background: 'linear-gradient(to right, #d1fae5, #10b981, #d1fae5)',
              }}
            />
            {steps.map((step) => (
              <div key={step.num} className="relative group">
                <div className="card text-center px-8 py-10 hover:border-accent-200 group-hover:-translate-y-1 transition-transform duration-300">
                  <div className="w-16 h-16 bg-accent-50 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:bg-accent-100 transition-colors">
                    <step.icon size={28} className="text-accent-500" />
                  </div>
                  <p className="text-xs font-bold text-accent-500 mb-2 tracking-widest">STEP {step.num}</p>
                  <h3 className="text-lg font-bold text-content-primary mb-3">{step.title}</h3>
                  <p className="text-sm text-content-secondary leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* === SCHEMES === */}
      <section id="schemes" className="section bg-surface-secondary">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-accent-500 uppercase tracking-wider mb-2">Knowledge Base</p>
            <h2 className="section-title text-center">What Can You Ask VaaniSeva?</h2>
            <p className="section-subtitle mx-auto mt-4">
              From crop prices to health coverage to legal rights — ask anything, in your language, right now.
            </p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {schemes.map((s) => (
              <Link key={s.name} to={`/try?q=${encodeURIComponent(s.name + ' के बारे में बताइए')}`} className="card flex items-start gap-4 hover:border-accent-200 cursor-pointer group">
                <div className="w-11 h-11 bg-accent-50 rounded-xl flex items-center justify-center text-xl flex-shrink-0 group-hover:bg-accent-100 transition-colors">
                  {s.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-content-primary text-sm group-hover:text-accent-600 transition-colors">{s.name}</h3>
                  <p className="font-hindi text-xs text-accent-600">{s.hindi}</p>
                  <p className="text-xs text-content-secondary mt-1 leading-relaxed">{s.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* === CTA === */}
      <section style={{ background: 'linear-gradient(135deg, #1a0f00 0%, #3d1f00 50%, #1a0f00 100%)' }}>
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-3" style={{ color: '#F0A832' }}>
            One Call. Any Language. Real Answers.
          </h2>
          <p className="text-lg text-white/75 mb-8 max-w-lg mx-auto">
            Built for the AI for Bharat Hackathon 2026.
            No signup needed — just call us now.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="tel:+19788309619" className="inline-flex items-center gap-2 px-8 py-4 font-bold rounded-xl text-lg text-white transition-colors shadow-lg hover:opacity-90" style={{ background: '#D4860B' }}>
              <Phone size={22} />
              +1 978 830 9619
            </a>
            <Link to="/try" className="inline-flex items-center gap-2 px-8 py-4 text-white font-bold rounded-xl text-lg hover:bg-white/10 transition-colors" style={{ border: '2px solid #D4860B' }}>
              Try on Web
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* === STICKY CALL ME BACK WIDGET === */}
      {!showCallWidget && (
        <button
          onClick={() => setShowCallWidget(true)}
          className="fixed bottom-6 right-[112px] z-50 bg-gradient-accent text-white px-5 py-3 rounded-full shadow-lg hover:opacity-90 active:scale-95 transition-all flex items-center gap-2 font-semibold text-sm"
        >
          <Phone size={18} />
          Call Me Back
        </button>
      )}

      {showCallWidget && (
        <div className="fixed bottom-6 right-[112px] z-50 w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden animate-slide-up">
          <div className="bg-gradient-accent px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-white">
              <Phone size={16} />
              <span className="font-semibold text-sm">Call Me Back</span>
            </div>
            <button onClick={() => setShowCallWidget(false)} className="text-white/80 hover:text-white">
              <X size={18} />
            </button>
          </div>
          <div className="p-4">
            <CallMeBack compact />
          </div>
        </div>
      )}

      {/* === FOOTER === */}
      <footer className="bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-12">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-9 h-9 bg-gradient-accent rounded-lg flex items-center justify-center">
                  <Phone size={18} className="text-white" />
                </div>
                <div className="flex flex-col leading-none">
                  <span className="font-bold text-lg text-content-primary">VaaniSeva</span>
                  <span className="text-[10px] text-content-tertiary font-medium tracking-wider uppercase">Voice AI for India</span>
                </div>
              </div>
              <p className="text-sm text-content-secondary leading-relaxed">
                Built by Team Prayas for AI for Bharat Hackathon 2026.
                VaaniSeva is a Voice-First AI helpline built to serve rural and underserved India — accessible from any basic phone, in any language.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-content-primary mb-3">Quick Links</h4>
              <div className="space-y-2">
                <a href="#how-it-works" className="block text-sm text-content-secondary hover:text-accent-500 transition-colors">How It Works</a>
                <a href="#schemes" className="block text-sm text-content-secondary hover:text-accent-500 transition-colors">Schemes</a>
                <Link to="/try" className="block text-sm text-content-secondary hover:text-accent-500 transition-colors">Try VaaniSeva</Link>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-content-primary mb-3">About</h4>
              <p className="text-sm text-content-secondary leading-relaxed">
                Built by <strong>Team Prayas</strong> for the <strong>AI for Bharat Hackathon 2026</strong>.
              </p>
              <p className="text-sm text-content-secondary mt-2">Problem Statement 3 — Voice AI for Rural India</p>
            </div>
          </div>
          <div className="mt-10 pt-6 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-content-tertiary">© 2026 VaaniSeva — Team Prayas. All rights reserved.</p>
            <span className="text-xs text-content-tertiary">Powered by AWS Bedrock + Sarvam AI + Twilio</span>
          </div>
        </div>
      </footer>
    </>
  )
}
