import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Check, Phone, Star, Briefcase } from 'lucide-react'

const plans = [
  {
    name: 'Free',
    hindi: 'मुफ़्त',
    price: '₹0',
    period: 'forever',
    icon: Phone,
    color: 'bg-gray-50 border-gray-200',
    buttonStyle: 'btn-secondary',
    features: [
      '10 calls per month',
      '4 languages supported',
      'Government scheme info',
      'Basic health guidance',
      'Agriculture basics',
    ],
  },
  {
    name: 'Pro',
    hindi: 'प्रो',
    price: '₹99',
    period: '/month',
    icon: Star,
    color: 'bg-accent-50 border-accent-300',
    buttonStyle: 'btn-primary',
    popular: true,
    features: [
      'Unlimited calls',
      'Full conversation history',
      'Personalized AI (remembers you)',
      'Priority response time',
      'SMS summaries after calls',
      'Custom context profile',
      'Scheme enrollment tracking',
    ],
  },
  {
    name: 'Business',
    hindi: 'व्यापार',
    price: 'Custom',
    period: '',
    icon: Briefcase,
    color: 'bg-gray-50 border-gray-200',
    buttonStyle: 'btn-secondary',
    features: [
      'Everything in Pro',
      'API access',
      'Custom knowledge base',
      'Dedicated support line',
      'Analytics dashboard',
      'Multi-user admin panel',
      'SLA guarantee',
    ],
  },
]

export default function Pricing() {
  return (
    <div className="min-h-screen bg-surface-secondary pt-20">
      <div className="max-w-6xl mx-auto px-6 md:px-12 py-12">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-content-secondary hover:text-accent-500 transition-colors mb-8">
          <ArrowLeft size={16} /> Back to Home
        </Link>

        <div className="text-center mb-12">
          <p className="text-sm font-semibold text-accent-500 uppercase tracking-wider mb-2">Pricing</p>
          <h1 className="text-3xl md:text-4xl font-bold text-content-primary mb-3">
            Simple, Fair Pricing
          </h1>
          <p className="text-lg text-content-secondary max-w-xl mx-auto">
            Start free. Upgrade when VaaniSeva becomes your go-to assistant.
          </p>
          <p className="font-hindi text-accent-600 text-sm mt-2">
            शुरुआत मुफ़्त है। जब वाणीसेवा आपकी ज़रूरत बन जाए, तब अपग्रेड करें।
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan) => (
            <div key={plan.name} className={`relative rounded-2xl border-2 p-8 ${plan.color} ${plan.popular ? 'shadow-lg scale-105 md:scale-105' : 'shadow-sm'}`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-accent text-white text-xs font-bold px-4 py-1 rounded-full">
                  Most Popular
                </div>
              )}

              <div className="flex items-center gap-3 mb-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${plan.popular ? 'bg-accent-100' : 'bg-gray-100'}`}>
                  <plan.icon size={20} className={plan.popular ? 'text-accent-600' : 'text-content-secondary'} />
                </div>
                <div>
                  <h3 className="font-bold text-content-primary text-lg">{plan.name}</h3>
                  <p className="font-hindi text-xs text-content-secondary">{plan.hindi}</p>
                </div>
              </div>

              <div className="mb-6">
                <span className="text-4xl font-bold text-content-primary">{plan.price}</span>
                {plan.period && <span className="text-content-secondary text-sm ml-1">{plan.period}</span>}
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm text-content-secondary">
                    <Check size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <button className={`${plan.buttonStyle} w-full`}>
                {plan.name === 'Business' ? 'Contact Us' : plan.name === 'Free' ? 'Get Started' : 'Coming Soon'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
