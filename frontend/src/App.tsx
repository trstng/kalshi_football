import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Nav } from './components/Nav'
import Dashboard from './pages/Dashboard'
import TradeHistory from './pages/TradeHistory'
import Analytics from './pages/Analytics'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-purple-950 to-slate-950">
        <Nav />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<TradeHistory />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
