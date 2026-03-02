import React from 'react'
import { Link } from 'react-router-dom'
import { Phone, ArrowRight, Mic, MessageCircle, Globe, Shield, Clock, Users, ChevronRight } from 'lucide-react'

// ── Scheme data ───────────────────────────────────────
const schemes = [
  { name: 'PM-Kisan',           hindi: 'पीएम किसान',             desc: 'Direct income support of ₹6,000/year to farmer families', icon: '🌾' },
  { name: 'Ayushman Bharat',    hindi: 'आयुष्मान भारत',          desc: 'Free health coverage up to ₹5 lakh per family per year', icon: '🏥' },
  { name: 'MGNREGA',            hindi: 'मनरेगा',                 desc: '100 days guaranteed employment for rural households', icon: '⚒️' },
  { name: 'PM Awas Yojana',     hindi: 'पीएम आवास योजना',        desc: 'Affordable housing for economically weaker sections', icon: '🏠' },
  { name: 'Sukanya Samriddhi',  hindi: 'सुकन्या समृद्धि',        desc: 'Savings scheme for girl child education & marriage', icon: '👧' },
  { name: 'PM Ujjwala',         hindi: 'पीएम उज्ज्वला',          desc: 'Free LPG connections for BPL households', icon: '🔥' },
  { name: 'Jan Dhan Yojana',    hindi: 'जन धन योजना',            desc: 'Zero-balance bank accounts with insurance cover', icon: '🏦' },
  { name: 'PM Mudra Yojana',    hindi: 'पीएम मुद्रा योजना',       desc: 'Collateral-free loans up to ₹10 lakh for small businesses', icon: '💼' },
  { name: 'Atal Pension',       hindi: 'अटल पेंशन योजना',        desc: 'Guaranteed pension of ₹1,000-5,000/month after 60', icon: '👴' },
]

// ── Steps data ────────────────────────────────────────
const steps = [
  {
    num: '01',
    title: 'Call the Number',
    titleHi: 'नंबर पर कॉल करें',
    desc: 'Dial from any phone — smartphone or basic keypad phone. No internet needed.',
    icon: Phone,
  },
  {
    num: '02',
    title: 'Ask Your Question',
    titleHi: 'अपना सवाल पूछें',
    desc: 'Speak in Hindi or English. Ask about any government scheme naturally.',
    icon: Mic,
  },
  {
    num: '03',
    title: 'Get Your Answer',
    titleHi: 'जवाब पाएं',
    desc: 'AI gives you accurate, simple answers you can understand and act on.',
    icon: MessageCircle,
  },
]

// ── Stats ─────────────────────────────────────────────
const stats = [
  { value: '30+', label: 'Government Schemes', icon: Shield },
  { value: '24/7', label: 'Always Available', icon: Clock },
  { value: '2', label: 'Languages (Hindi & English)', icon: Globe },
  { value: '500M+', label: 'Indians We Aim to Serve', icon: Users },
]

// ══════════════════════════════════════════════════════
export default function Home() {
  return (
    <>
      {/* ═══ HERO SECTION ═══════════════════════════════ */}
      <section className="relative h-screen w-full overflow-hidden">
        {/* Background Video */}
        <video
          className="absolute inset-0 w-full h-full object-cover"
          src="/hero.mp4"
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        />

        {/* Left gradient overlay for text readability */}
        <div className="absolute inset-0 bg-gradient-hero" />

        {/* Content */}
        <div className="relative z-10 h-full flex items-center">
          <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 w-full">
            <div className="max-w-xl">
              {/* Eyebrow */}
              <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 mb-6">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span className="text-white/90 text-sm font-medium">Live Now — Call Anytime</span>
              </div>

              {/* Title */}
              <h1 className="font-hindi text-5xl md:text-7xl font-extrabold text-white leading-tight mb-2">
                वाणीसेवा
              </h1>
              <p className="text-xl md:text-2xl font-semibold text-white/90 mb-6">
                Voice AI for Every Indian
              </p>

              {/* Tagline */}
              <p className="text-base md:text-lg text-white/70 mb-8 leading-relaxed max-w-md">
                Access information about 30+ government schemes by simply making a phone call.
                <span className="block mt-1 font-hindi text-white/50">
                  किसी भी फ़ोन से कॉल करें — स्मार्टफ़ोन ज़रूरी नहीं
                </span>
              </p>

              {/* CTAs */}
              <div className="flex flex-wrap items-center gap-4">
                <a href="tel:+12602048966" className="btn-primary text-base">
                  <Phone size={18} />
                  Call +1 260 204 8966
                </a>
                <Link to="/try" className="btn-ghost text-base">
                  Try on Web
                  <ArrowRight size={16} />
                </Link>
              </div>

              {/* Footnote */}
              <p className="mt-6 text-xs text-white/40">
                No smartphone needed &nbsp;·&nbsp; No internet required &nbsp;·&nbsp; Works on ₹500 phones
              </p>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center pt-2">
            <div className="w-1 h-2.5 bg-white/50 rounded-full" />
          </div>
        </div>
      </section>

      {/* ═══ STATS BAR ══════════════════════════════════ */}
      <section className="bg-surface-secondary border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-saffron-50 rounded-xl flex items-center justify-center">
                  <s.icon size={20} className="text-saffron-500" />
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

      {/* ═══ HOW IT WORKS ═══════════════════════════════ */}
      <section id="how-it-works" className="section bg-white">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-saffron-500 uppercase tracking-wider mb-2">Simple Process</p>
            <h2 className="section-title text-center">
              <span className="font-hindi">कैसे काम करता है?</span>
              <span className="block text-2xl text-content-secondary font-normal mt-1">How It Works</span>
            </h2>
          </div>

          {/* Steps */}
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <div key={step.num} className="relative group">
                <div className="card text-center px-8 py-10 hover:border-saffron-200 group-hover:-translate-y-1 transition-transform duration-300">
                  <div className="w-16 h-16 bg-saffron-50 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:bg-saffron-100 transition-colors">
                    <step.icon size={28} className="text-saffron-500" />
                  </div>
                  <p className="text-xs font-bold text-saffron-500 mb-2">STEP {step.num}</p>
                  <h3 className="text-lg font-bold text-content-primary mb-1">{step.title}</h3>
                  <p className="font-hindi text-sm text-saffron-600 mb-3">{step.titleHi}</p>
                  <p className="text-sm text-content-secondary leading-relaxed">{step.desc}</p>
                </div>
                {/* Arrow connector */}
                {i < steps.length - 1 && (
                  <div className="hidden md:flex absolute top-1/2 -right-4 -translate-y-1/2 z-10">
                    <ChevronRight size={24} className="text-gray-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ SCHEMES ════════════════════════════════════ */}
      <section id="schemes" className="section bg-surface-secondary">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-saffron-500 uppercase tracking-wider mb-2">Knowledge Base</p>
            <h2 className="section-title text-center">
              <span className="font-hindi">सरकारी योजनाएँ</span>
              <span className="block text-2xl text-content-secondary font-normal mt-1">Government Schemes We Cover</span>
            </h2>
            <p className="section-subtitle mx-auto mt-4">
              Ask VaaniSeva about any of these schemes in Hindi or English. Get eligibility, benefits, and how to apply.
            </p>
          </div>

          {/* Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {schemes.map((s) => (
              <div
                key={s.name}
                className="card flex items-start gap-4 hover:border-saffron-200 cursor-default"
              >
                <div className="w-11 h-11 bg-saffron-50 rounded-xl flex items-center justify-center text-xl flex-shrink-0">
                  {s.icon}
                </div>
                <div>
                  <h3 className="font-semibold text-content-primary text-sm">{s.name}</h3>
                  <p className="font-hindi text-xs text-saffron-600">{s.hindi}</p>
                  <p className="text-xs text-content-secondary mt-1 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA BANNER ═════════════════════════════════ */}
      <section className="bg-gradient-saffron">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-16 text-center">
          <h2 className="font-hindi text-3xl md:text-4xl font-bold text-white mb-3">
            अभी कॉल करें
          </h2>
          <p className="text-lg text-white/80 mb-8 max-w-lg mx-auto">
            Try VaaniSeva right now — call from any phone or test it directly on the web
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="tel:+12602048966"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-saffron-600 font-bold rounded-xl text-lg hover:bg-gray-50 transition-colors shadow-lg"
            >
              <Phone size={22} />
              +1 260 204 8966
            </a>
            <Link
              to="/try"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 text-white font-bold rounded-xl text-lg border-2 border-white/30 hover:bg-white/20 transition-colors"
            >
              Try on Web
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═════════════════════════════════════ */}
      <footer className="bg-white border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-6 md:px-12 lg:px-20 py-12">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-9 h-9 bg-gradient-saffron rounded-lg flex items-center justify-center">
                  <Phone size={18} className="text-white" />
                </div>
                <div className="flex flex-col leading-none">
                  <span className="font-hindi font-bold text-lg text-content-primary">वाणीसेवा</span>
                  <span className="text-[10px] text-content-tertiary font-medium tracking-wider uppercase">VaaniSeva</span>
                </div>
              </div>
              <p className="text-sm text-content-secondary leading-relaxed">
                AI-powered voice assistant enabling 500M+ rural Indians to access government scheme information via a simple phone call.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold text-sm text-content-primary mb-3">Quick Links</h4>
              <div className="space-y-2">
                <a href="#how-it-works" className="block text-sm text-content-secondary hover:text-saffron-500 transition-colors">How It Works</a>
                <a href="#schemes" className="block text-sm text-content-secondary hover:text-saffron-500 transition-colors">Schemes</a>
                <Link to="/try" className="block text-sm text-content-secondary hover:text-saffron-500 transition-colors">Try VaaniSeva</Link>
              </div>
            </div>

            {/* Hackathon */}
            <div>
              <h4 className="font-semibold text-sm text-content-primary mb-3">About</h4>
              <p className="text-sm text-content-secondary leading-relaxed">
                Built by <strong>Team Prayas</strong> for the <strong>AI for Bharat Hackathon 2026</strong>.
              </p>
              <p className="text-sm text-content-secondary mt-2">
                Problem Statement 3 — Voice AI for Rural India
              </p>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-content-tertiary">
              © 2026 VaaniSeva — Team Prayas. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-content-tertiary">
                Powered by AWS Bedrock + Sarvam AI + Twilio
              </span>
            </div>
          </div>
        </div>
      </footer>
    </>
  )
}
