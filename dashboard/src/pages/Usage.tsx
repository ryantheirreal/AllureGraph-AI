import { BarChart3, TrendingUp, Calendar } from 'lucide-react'

const dailyUsage = [
  { day: 'Mon', scrapes: 45 },
  { day: 'Tue', scrapes: 62 },
  { day: 'Wed', scrapes: 38 },
  { day: 'Thu', scrapes: 71 },
  { day: 'Fri', scrapes: 55 },
  { day: 'Sat', scrapes: 28 },
  { day: 'Sun', scrapes: 19 },
]

const byTemplate = [
  { template: 'product_prices', count: 89, percent: 28 },
  { template: 'telegram_channel', count: 67, percent: 21 },
  { template: 'competitor_offers', count: 54, percent: 17 },
  { template: 'instagram_profile', count: 43, percent: 13 },
  { template: 'lead_enrichment', count: 38, percent: 12 },
  { template: 'other', count: 27, percent: 9 },
]

export default function Usage() {
  const maxScrapes = Math.max(...dailyUsage.map(d => d.scrapes))

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Usage & Billing</h1>

      {/* Current Period */}
      <div className="glass rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm text-zinc-500">Current Period</div>
            <div className="text-lg font-semibold">Jul 1 — Jul 31, 2026</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-zinc-500">Plan: Pro ($99/mo)</div>
            <div className="text-lg font-semibold text-purple-400">3,753 / 5,000</div>
          </div>
        </div>
        <div className="w-full bg-white/10 rounded-full h-3">
          <div className="bg-gradient-to-r from-purple-600 to-blue-500 h-3 rounded-full transition-all" style={{ width: '75%' }} />
        </div>
        <div className="flex justify-between mt-2 text-xs text-zinc-500">
          <span>75% used</span>
          <span>1,247 remaining</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Chart */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-sm font-medium text-zinc-400 mb-4 flex items-center gap-2">
            <Calendar className="w-4 h-4" /> This Week
          </h3>
          <div className="flex items-end gap-2 h-32">
            {dailyUsage.map(d => (
              <div key={d.day} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full bg-purple-500/40 rounded-t hover:bg-purple-500/60 transition"
                  style={{ height: `${(d.scrapes / maxScrapes) * 100}%` }}
                />
                <span className="text-xs text-zinc-500">{d.day}</span>
              </div>
            ))}
          </div>
        </div>

        {/* By Template */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-sm font-medium text-zinc-400 mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> By Template
          </h3>
          <div className="space-y-3">
            {byTemplate.map(t => (
              <div key={t.template}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-zinc-300">{t.template}</span>
                  <span className="text-zinc-500">{t.count} scrapes</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-1.5">
                  <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${t.percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
