import { Eye, Plus, Pause, Play, Trash2 } from 'lucide-react'

const monitors = [
  { id: 1, name: 'ApexVips Pricing', url: 'apexvips.com/pricing', frequency: 'daily', status: 'active', lastCheck: '2h ago', changes: 0 },
  { id: 2, name: 'Astrofy Plans', url: 'astrofy.io/plans', frequency: 'daily', status: 'active', lastCheck: '4h ago', changes: 2 },
  { id: 3, name: 'Shopee Nicho X', url: 'shopee.com.br/search?q=...', frequency: 'hourly', status: 'active', lastCheck: '15min ago', changes: 5 },
  { id: 4, name: 'Telegram Concorrente', url: 't.me/s/channelx', frequency: 'daily', status: 'paused', lastCheck: '2d ago', changes: 0 },
]

export default function Monitor() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Monitor</h1>
          <p className="text-zinc-500 text-sm mt-1">Track competitors and market changes automatically</p>
        </div>
        <button className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm font-medium transition">
          <Plus className="w-4 h-4" /> New Monitor
        </button>
      </div>

      <div className="space-y-3">
        {monitors.map(m => (
          <div key={m.id} className="glass rounded-xl p-5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-2 h-2 rounded-full ${m.status === 'active' ? 'bg-emerald-400' : 'bg-zinc-600'}`} />
              <div>
                <div className="font-medium">{m.name}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{m.url}</div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-xs text-zinc-400">{m.frequency}</div>
                <div className="text-xs text-zinc-600">Last: {m.lastCheck}</div>
              </div>

              {m.changes > 0 && (
                <span className="bg-amber-500/20 text-amber-400 text-xs px-2 py-0.5 rounded-full">
                  {m.changes} changes
                </span>
              )}

              <div className="flex gap-1">
                <button className="p-2 hover:bg-white/10 rounded-lg transition">
                  {m.status === 'active' ? <Pause className="w-4 h-4 text-zinc-400" /> : <Play className="w-4 h-4 text-zinc-400" />}
                </button>
                <button className="p-2 hover:bg-white/10 rounded-lg transition">
                  <Trash2 className="w-4 h-4 text-zinc-400" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
