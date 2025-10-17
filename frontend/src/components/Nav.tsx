import { Link, useLocation } from 'react-router-dom'

export function Nav() {
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-purple-500/20">
      <div className="max-w-7xl mx-auto px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 blur-lg opacity-50"></div>
              <div className="relative w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            </div>
            <div>
              <div className="text-xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Kalshi NFL
              </div>
              <div className="text-xs text-gray-500 font-semibold -mt-1">Live Trading System</div>
            </div>
          </div>

          <div className="flex gap-2">
            <Link
              to="/"
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                isActive('/')
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/schedule"
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                isActive('/schedule')
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Schedule
            </Link>
            <Link
              to="/history"
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                isActive('/history')
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              History
            </Link>
            <Link
              to="/analytics"
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                isActive('/analytics')
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Analytics
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
