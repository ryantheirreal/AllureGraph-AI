import { useState } from 'react'
import { Key, Copy, Plus, Trash2, Eye, EyeOff } from 'lucide-react'

const mockKeys = [
  { id: 1, name: 'Production', key: 'ag_live_7f8a9b2c3d4e5f6a7b8c', created: '2026-07-01', lastUsed: '2min ago' },
  { id: 2, name: 'Development', key: 'ag_test_1a2b3c4d5e6f7a8b9c0d', created: '2026-06-28', lastUsed: '1d ago' },
]

export default function ApiKeys() {
  const [showKey, setShowKey] = useState<number | null>(null)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-zinc-500 text-sm mt-1">Manage your API authentication keys</p>
        </div>
        <button className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm font-medium transition">
          <Plus className="w-4 h-4" /> Create Key
        </button>
      </div>

      {/* Quick Start */}
      <div className="glass rounded-xl p-5 mb-6">
        <h3 className="text-sm font-medium text-zinc-400 mb-3">Quick Start</h3>
        <pre className="bg-black/50 rounded-lg p-4 text-sm text-zinc-300 overflow-x-auto">
{`curl -X POST https://graph.allurevips.fun/api/scrape \\
  -H "Authorization: Bearer ag_live_YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "prompt": "Extract prices"}'`}
        </pre>
      </div>

      {/* Keys List */}
      <div className="space-y-3">
        {mockKeys.map(k => (
          <div key={k.id} className="glass rounded-xl p-5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Key className="w-5 h-5 text-purple-400" />
              <div>
                <div className="font-medium">{k.name}</div>
                <div className="font-mono text-sm text-zinc-500 mt-0.5">
                  {showKey === k.id ? k.key : k.key.slice(0, 12) + '••••••••••'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right text-xs text-zinc-500">
                <div>Created: {k.created}</div>
                <div>Last used: {k.lastUsed}</div>
              </div>
              <div className="flex gap-1">
                <button onClick={() => setShowKey(showKey === k.id ? null : k.id)} className="p-2 hover:bg-white/10 rounded-lg transition">
                  {showKey === k.id ? <EyeOff className="w-4 h-4 text-zinc-400" /> : <Eye className="w-4 h-4 text-zinc-400" />}
                </button>
                <button className="p-2 hover:bg-white/10 rounded-lg transition">
                  <Copy className="w-4 h-4 text-zinc-400" />
                </button>
                <button className="p-2 hover:bg-white/10 rounded-lg transition">
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
