import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Scraper from './pages/Scraper'
import Templates from './pages/Templates'
import Monitor from './pages/Monitor'
import ApiKeys from './pages/ApiKeys'
import Usage from './pages/Usage'
import Landing from './pages/Landing'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/scrape" element={<Scraper />} />
        <Route path="/templates" element={<Templates />} />
        <Route path="/monitor" element={<Monitor />} />
        <Route path="/api-keys" element={<ApiKeys />} />
        <Route path="/usage" element={<Usage />} />
      </Route>
    </Routes>
  )
}
