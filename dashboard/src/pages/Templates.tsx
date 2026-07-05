import { FileText, Star, ArrowRight } from 'lucide-react'

const templates = [
  { slug: 'telegram_channel', name: 'Telegram Channel', category: 'social', credits: 2, popular: true },
  { slug: 'instagram_profile', name: 'Instagram Profile', category: 'social', credits: 3, popular: true },
  { slug: 'x_profile', name: 'X/Twitter Profile', category: 'social', credits: 2, popular: false },
  { slug: 'product_prices', name: 'Product Prices', category: 'ecommerce', credits: 1, popular: true },
  { slug: 'mercadolivre_products', name: 'Mercado Livre', category: 'ecommerce', credits: 2, popular: true },
  { slug: 'shopee_products', name: 'Shopee Products', category: 'ecommerce', credits: 2, popular: false },
  { slug: 'competitor_offers', name: 'Competitor Offers', category: 'intelligence', credits: 2, popular: true },
  { slug: 'saas_pricing', name: 'SaaS Pricing', category: 'intelligence', credits: 2, popular: false },
  { slug: 'lead_enrichment', name: 'Lead Enrichment', category: 'leads', credits: 3, popular: false },
  { slug: 'linkedin_company', name: 'LinkedIn Company', category: 'leads', credits: 3, popular: false },
  { slug: 'review_aggregator', name: 'Review Aggregator', category: 'social_proof', credits: 2, popular: false },
  { slug: 'google_reviews', name: 'Google Reviews', category: 'social_proof', credits: 2, popular: false },
  { slug: 'content_research', name: 'Content Research', category: 'content', credits: 3, popular: false },
  { slug: 'trending_hashtags', name: 'Trending Hashtags', category: 'content', credits: 2, popular: false },
]

const categoryColors: Record<string, string> = {
  social: 'bg-blue-500/20 text-blue-400',
  ecommerce: 'bg-emerald-500/20 text-emerald-400',
  intelligence: 'bg-purple-500/20 text-purple-400',
  leads: 'bg-amber-500/20 text-amber-400',
  social_proof: 'bg-pink-500/20 text-pink-400',
  content: 'bg-cyan-500/20 text-cyan-400',
}

export default function Templates() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Templates</h1>
      <p className="text-zinc-500 mb-6">Pre-built extraction templates for common tasks</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map(t => (
          <div key={t.slug} className="glass rounded-xl p-5 hover:border-purple-500/30 transition cursor-pointer group">
            <div className="flex items-start justify-between mb-3">
              <FileText className="w-5 h-5 text-purple-400" />
              {t.popular && <Star className="w-4 h-4 text-amber-400 fill-amber-400" />}
            </div>
            <h3 className="font-semibold mb-1">{t.name}</h3>
            <div className="flex items-center gap-2 mb-3">
              <span className={`text-xs px-2 py-0.5 rounded-full ${categoryColors[t.category]}`}>
                {t.category}
              </span>
              <span className="text-xs text-zinc-500">{t.credits} credits</span>
            </div>
            <div className="flex items-center text-sm text-purple-400 opacity-0 group-hover:opacity-100 transition">
              Use template <ArrowRight className="w-3 h-3 ml-1" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
