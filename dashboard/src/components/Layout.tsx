import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Search, FileText, Eye,
  Key, BarChart3, Zap, LogOut
} from 'lucide-react'

const nav = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/scrape', label: 'Scraper', icon: Search },
  { path: '/templates', label: 'Templates', icon: FileText },
  { path: '/monitor', label: 'Monitor', icon: Eye },
  { path: '/api-keys', label: 'API Keys', icon: Key },
  { path: '/usage', label: 'Usage', icon: BarChart3 },
]

export default function Layout() {
  const { pathname } = useLocation()

  return (
    <div className="flex h-screen bg-black">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/10 flex flex-col">
        <div className="p-6">
          <Link to="/dashboard" className="flex items-center gap-2">
            <Zap className="w-6 h-6 text-purple-400" />
            <span className="text-lg font-bold gradient-text">AllureGraph</span>
          </Link>
        </div>

        <nav className="flex-1 px-3">
          {nav.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 transition-all ${
                pathname === item.path
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : 'text-zinc-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <item.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="glass rounded-lg p-3">
            <div className="text-xs text-zinc-500">Plan: Pro</div>
            <div className="text-sm font-medium mt-1">3,753 / 5,000 credits</div>
            <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
              <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: '75%' }} />
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
