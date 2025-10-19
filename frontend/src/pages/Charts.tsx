import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import CandlestickChart from '../components/CandlestickChart'
import { fetchGamesWithData, fetchGameTicks, fetchTradeMarkers, aggregateTicksToCandles } from '../lib/chartHelpers'
import type { Candle, TradeMarker } from '../lib/chartHelpers'

interface GameOption {
  id: string
  title: string
  ticker: string
  kickoff_ts: number
}

export default function Charts() {
  const [games, setGames] = useState<GameOption[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string>('')
  const [candles, setCandles] = useState<Candle[]>([])
  const [markers, setMarkers] = useState<TradeMarker[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingChart, setLoadingChart] = useState(false)

  useEffect(() => {
    loadGames()
  }, [])

  useEffect(() => {
    if (selectedGameId) {
      loadChartData(selectedGameId)
    }
  }, [selectedGameId])

  async function loadGames() {
    setLoading(true)
    const gamesData = await fetchGamesWithData()
    setGames(gamesData)
    setLoading(false)

    // Auto-select the first game if available
    if (gamesData.length > 0) {
      setSelectedGameId(gamesData[0].id)
    }
  }

  async function loadChartData(gameId: string) {
    setLoadingChart(true)

    // Fetch ticks and markers in parallel
    const [ticks, tradeMarkers] = await Promise.all([
      fetchGameTicks(gameId),
      fetchTradeMarkers(gameId),
    ])

    // Aggregate ticks into candles
    const candlesData = aggregateTicksToCandles(ticks)

    setCandles(candlesData)
    setMarkers(tradeMarkers)
    setLoadingChart(false)
  }

  const selectedGame = games.find(g => g.id === selectedGameId)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Market Charts
          </h1>
          <p className="text-gray-400 text-lg">Historical price action with entry/exit markers</p>
        </div>

        {/* Game Selector */}
        {loading ? (
          <div className="mb-8 flex items-center justify-center h-20">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse delay-75"></div>
              <div className="w-3 h-3 bg-pink-500 rounded-full animate-pulse delay-150"></div>
              <span className="text-gray-400 ml-2">Loading games...</span>
            </div>
          </div>
        ) : games.length === 0 ? (
          <div className="mb-8 relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-12">
              <div className="flex flex-col items-center gap-3">
                <svg className="w-20 h-20 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-gray-400 text-lg font-semibold">No games with chart data available</p>
                <p className="text-gray-500 text-sm">Games will appear here after market data is collected</p>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-8 relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
                <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">
                  Select Game
                </label>
                <select
                  value={selectedGameId}
                  onChange={(e) => setSelectedGameId(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                >
                  {games.map((game) => (
                    <option key={game.id} value={game.id}>
                      {game.title} ({game.ticker}) - {format(new Date(game.kickoff_ts * 1000), 'MMM d, yyyy')}
                    </option>
                  ))}
                </select>
                {selectedGame && (
                  <div className="mt-3 flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-gray-400">
                      Showing data for: <span className="text-white font-semibold">{selectedGame.ticker}</span>
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Chart Container */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></div>
                    Price Chart (1-Minute Candles)
                  </h2>
                </div>
                <div className="p-6">
                  {loadingChart ? (
                    <div className="flex items-center justify-center h-[600px]">
                      <div className="flex flex-col items-center gap-4">
                        <div className="flex items-center gap-3">
                          <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
                          <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse delay-75"></div>
                          <div className="w-4 h-4 bg-pink-500 rounded-full animate-pulse delay-150"></div>
                        </div>
                        <span className="text-gray-400 text-lg font-semibold">Loading chart data...</span>
                      </div>
                    </div>
                  ) : (
                    <CandlestickChart candles={candles} markers={markers} />
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
