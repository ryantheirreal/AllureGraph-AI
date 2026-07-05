import { BarChart3, Zap, Clock, TrendingUp } from 'lucide-react'

const stats = [
  { label: 'Scrapes Today', value: '247', icon: Zap, trend: '+12%' },
  { label: 'Credits Used', value: '3,753', icon: BarChart3, trend: '75%' },
  { label: 'Avg Response', value: '2.3s', icon: Clock, trend: '-0.4s' },
  { label: 'Success Rate', value: '98.2%', icon: TrendingUp, trend: '+1.1%' },
]

const recentScrapes = [
  { id: 1, url: 'shopee.com.br/products', template: 'product_prices', status: 'completed', credits: 2, time: '1.8s' },
  { id: 2, url: 't.me/s/cryptobr', template: 'telegram_channel', status: 'completed', credits: 2, time: '3.2s' },
  { id: 3, url: 'instagram.com/lojax', template: 'instagram_profile', status: 'completed', credits: 3, time: '4.1s' },
  { id: 4, url: 'competitor.com/pricing', template: 'competitor_offers', status: 'processing', credits: 2, time: '-' },
  { id: 5, url: 'mercadolivre.com.br/...', template: 'mercadolivre_products', status: 'completed', credits: 2, time: '2.7s' },
]

export default function Dashboard() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(stat => (
          <div key={stat.label} className="glass rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <stat.icon className="w-5 h-5 text-purple-400" />
              <span className="text-xs text-emerald-400 font-medium">{stat.trend}</span>
            </div>
            <div className="text-2xl font-bold">{stat.value}</div>
            <div className="text-sm text-zinc-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Recent Scrapes */}
      <div className="glass rounded-xl">
        <div className="p-5 border-b border-white/10">
          <h2 className="text-lg font-semibold">Recent Scrapes</h2>
        </div>
        <div className="divide-y divide-white/5">
          {recentScrapes.map(scrape => (
            <div key={scrape.id} className="flex items-center justify-between px-5 py-3 hover:bg-white/5 transition">
              <div className="flex-1">
                <div className="text-sm font-medium truncate max-w-xs">{scrape.url}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{scrape.template}</div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-zinc-400">{scrape.credits} credits</span>
                <span className="text-xs text-zinc-400">{scrape.time}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  scrape.status === 'completed'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  {scrape.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
