import { Zap, Search, Eye, FileText, Shield, Globe, ArrowRight, Check } from 'lucide-react'
import { Link } from 'react-router-dom'

const features = [
  { icon: Search, title: 'AI-Powered Extraction', desc: 'Tell it what you want in plain language. The AI understands any page structure.' },
  { icon: Eye, title: 'Competitor Monitoring', desc: 'Track pricing, features, and promotions. Get alerts when things change.' },
  { icon: FileText, title: '15+ Templates', desc: 'Telegram, Instagram, X, Shopee, Mercado Livre — ready to use.' },
  { icon: Shield, title: 'Anti-Detection', desc: 'Rotating proxies, headless browsers, human-like patterns built in.' },
  { icon: Globe, title: 'Multi-LLM', desc: 'Use GPT-4o, Claude, or your own Ollama models. Your choice.' },
  { icon: Zap, title: 'Blazing Fast', desc: 'Average 2.3s per scrape. Batch 100 URLs in parallel.' },
]

const plans = [
  { name: 'Starter', price: 29, credits: '500', features: ['API access', '5 templates', 'JSON/CSV export', '2 monitors'] },
  { name: 'Pro', price: 99, credits: '5,000', features: ['All templates', 'Webhooks', '20 monitors', 'Priority queue', 'Custom prompts'], popular: true },
  { name: 'Business', price: 299, credits: '25,000', features: ['Custom templates', 'SLA 99.9%', '100 monitors', 'Dedicated queue', 'API analytics'] },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-black">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Zap className="w-6 h-6 text-purple-400" />
          <span className="text-lg font-bold gradient-text">AllureGraph AI</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="#pricing" className="text-sm text-zinc-400 hover:text-white transition">Pricing</a>
          <a href="/docs" className="text-sm text-zinc-400 hover:text-white transition">Docs</a>
          <Link to="/dashboard" className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm font-medium transition">
            Dashboard
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-24 text-center max-w-4xl mx-auto">
        <div className="inline-block bg-purple-500/10 border border-purple-500/30 rounded-full px-4 py-1 text-sm text-purple-300 mb-6">
          ✨ AI-powered scraping for social sellers
        </div>
        <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-6">
          Extract <span className="gradient-text">anything</span> from<br />
          any website with AI
        </h1>
        <p className="text-xl text-zinc-400 mb-8 max-w-2xl mx-auto">
          Tell AllureGraph what you want in plain language. It scrapes, extracts, and delivers
          structured data — products, leads, reviews, competitors — in seconds.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link to="/dashboard" className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-6 py-3 rounded-lg font-medium transition glow-purple">
            Start Free <ArrowRight className="w-4 h-4" />
          </Link>
          <a href="/docs" className="flex items-center gap-2 border border-white/20 hover:border-white/40 px-6 py-3 rounded-lg font-medium transition">
            View Docs
          </a>
        </div>

        {/* Code snippet */}
        <div className="mt-12 glass rounded-xl p-6 text-left max-w-2xl mx-auto">
          <pre className="text-sm text-zinc-300 overflow-x-auto">
{`curl -X POST https://graph.allurevips.fun/api/scrape \\
  -H "Authorization: Bearer ag_live_xxx" \\
  -d '{
    "url": "https://shopee.com.br/search?q=iphone",
    "prompt": "Extract product names, prices, ratings",
    "template": "shopee_products"
  }'`}
          </pre>
        </div>
      </section>

      {/* Features */}
      <section className="px-6 py-20 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Built for social sellers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(f => (
            <div key={f.title} className="glass rounded-xl p-6">
              <f.icon className="w-8 h-8 text-purple-400 mb-4" />
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-zinc-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-6 py-20 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4">Simple, transparent pricing</h2>
        <p className="text-center text-zinc-500 mb-12">Start free. Scale as you grow.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(p => (
            <div key={p.name} className={`glass rounded-xl p-6 relative ${
              p.popular ? 'border-purple-500/50 glow-purple' : ''
            }`}>
              {p.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600 text-xs px-3 py-1 rounded-full font-medium">
                  Most Popular
                </div>
              )}
              <h3 className="text-xl font-bold mb-1">{p.name}</h3>
              <div className="mb-4">
                <span className="text-3xl font-bold">${p.price}</span>
                <span className="text-zinc-500">/mo</span>
              </div>
              <div className="text-sm text-purple-300 mb-4">{p.credits} scrapes/month</div>
              <ul className="space-y-2 mb-6">
                {p.features.map(f => (
                  <li key={f} className="flex items-center gap-2 text-sm text-zinc-300">
                    <Check className="w-4 h-4 text-emerald-400" /> {f}
                  </li>
                ))}
              </ul>
              <button className={`w-full py-2.5 rounded-lg font-medium transition ${
                p.popular ? 'bg-purple-600 hover:bg-purple-500' : 'bg-white/10 hover:bg-white/20'
              }`}>
                Get Started
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 px-6 py-8 text-center text-sm text-zinc-600">
        © 2026 AllureGraph AI — AllureVIPs LLC. All rights reserved.
      </footer>
    </div>
  )
}
