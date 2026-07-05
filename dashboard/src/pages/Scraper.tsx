import { useState } from 'react'
import { Search, Loader2, Copy, Download } from 'lucide-react'

export default function Scraper() {
  const [url, setUrl] = useState('')
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const handleScrape = async () => {
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setResult(JSON.stringify({
        products: [
          { name: 'Product 1', price: 'R$ 49,90', rating: 4.8 },
          { name: 'Product 2', price: 'R$ 89,90', rating: 4.5 },
        ]
      }, null, 2))
      setLoading(false)
    }, 2000)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Smart Scraper</h1>

      <div className="glass rounded-xl p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm text-zinc-400 mb-1 block">URL to scrape</label>
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder="https://example.com/products"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-purple-500/50"
            />
          </div>

          <div>
            <label className="text-sm text-zinc-400 mb-1 block">What to extract (natural language)</label>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Extract all product names, prices, ratings, and availability"
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-purple-500/50 resize-none"
            />
          </div>

          <div className="flex items-center gap-4">
            <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-300">
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="markdown">Markdown</option>
            </select>

            <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-zinc-300">
              <option value="openai">GPT-4o</option>
              <option value="anthropic">Claude Sonnet</option>
              <option value="ollama">Ollama (local)</option>
            </select>

            <button
              onClick={handleScrape}
              disabled={!url || !prompt || loading}
              className="ml-auto flex items-center gap-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 px-5 py-2.5 rounded-lg font-medium transition"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              {loading ? 'Scraping...' : 'Scrape'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="glass rounded-xl">
          <div className="flex items-center justify-between p-4 border-b border-white/10">
            <span className="text-sm font-medium text-emerald-400">✓ Extraction complete — 1 credit used</span>
            <div className="flex gap-2">
              <button className="p-2 hover:bg-white/10 rounded-lg transition">
                <Copy className="w-4 h-4 text-zinc-400" />
              </button>
              <button className="p-2 hover:bg-white/10 rounded-lg transition">
                <Download className="w-4 h-4 text-zinc-400" />
              </button>
            </div>
          </div>
          <pre className="p-4 text-sm text-zinc-300 overflow-auto max-h-96">
            <code>{result}</code>
          </pre>
        </div>
      )}
    </div>
  )
}
