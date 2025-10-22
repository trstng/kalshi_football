import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import LivePriceChart from '../components/LivePriceChart'
import LiveCandlestickChart from '../components/LiveCandlestickChart'
import TradeHistoryTable from '../components/TradeHistoryTable'
import {
  fetchMarkets,
  fetchLatestPrice,
  type Market,
  type LatestPrice,
} from '../lib/liveChartApi'

type Sport = 'NFL' | 'NHL' | 'NBA' | 'CFB'

export default function LiveCharts() {
  const [selectedSport, setSelectedSport] = useState<Sport>('NFL')
  const [markets, setMarkets] = useState<Market[]>([])
  const [selectedTicker, setSelectedTicker] = useState<string>('')
  const [latestPrice, setLatestPrice] = useState<LatestPrice | null>(null)
  const [chartType, setChartType] = useState<'line' | 'candle'>('line')
  const [loading, setLoading] = useState(true)
  const [priceLoading, setPriceLoading] = useState(false)

  // Load markets on mount and when sport changes
  useEffect(() => {
    loadMarkets()
  }, [selectedSport])

  // Load latest price when ticker changes
  useEffect(() => {
    if (selectedTicker) {
      loadLatestPrice()
      // Set up polling for latest price
      const interval = setInterval(loadLatestPrice, 5000) // Update every 5 seconds
      return () => clearInterval(interval)
    }
  }, [selectedTicker])

  async function loadMarkets() {
    setLoading(true)
    try {
      const data = await fetchMarkets()

      // Handle case where all markets are in "OTHER" category
      // Extract sport from ticker and filter accordingly
      let allMarkets = data.markets[selectedSport] || data.markets.OTHER || []

      // If markets are in OTHER, filter by sport based on ticker prefix
      if (!data.markets[selectedSport] && data.markets.OTHER) {
        // Map sport to ticker prefix
        const sportPrefixMap: Record<Sport, string> = {
          NFL: 'KXNFLGAME-',
          NHL: 'KXNHLGAME-',
          NBA: 'KXNBAGAME-',
          CFB: 'KXNCAAFGAME-',
        }

        const prefix = sportPrefixMap[selectedSport]
        allMarkets = data.markets.OTHER.filter((m: Market) =>
          m.ticker.startsWith(prefix)
        )
      }

      setMarkets(allMarkets)

      // Auto-select the first market if available
      if (allMarkets.length > 0 && !selectedTicker) {
        setSelectedTicker(allMarkets[0].ticker)
      }
    } catch (error) {
      console.error('Error loading markets:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadLatestPrice() {
    if (!selectedTicker) return

    setPriceLoading(true)
    try {
      const price = await fetchLatestPrice(selectedTicker)
      setLatestPrice(price)
    } catch (error) {
      console.error('Error loading latest price:', error)
    } finally {
      setPriceLoading(false)
    }
  }

  const selectedMarket = markets.find(m => m.ticker === selectedTicker)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Live Market Charts
          </h1>
          <p className="text-gray-400 text-lg">
            Real-time market data from WebSocket stream
          </p>
        </div>

        {/* Sport Selector */}
        <div className="mb-6 flex gap-3">
          {(['NFL', 'NHL', 'NBA', 'CFB'] as Sport[]).map((sport) => (
            <button
              key={sport}
              onClick={() => {
                setSelectedSport(sport)
                setSelectedTicker('') // Reset selection
              }}
              className={`px-6 py-3 rounded-xl font-bold transition-all ${
                selectedSport === sport
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50'
              }`}
            >
              {sport}
            </button>
          ))}
        </div>

        {/* Market Selector */}
        {loading ? (
          <div className="mb-8 flex items-center justify-center h-20">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
              <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse delay-75"></div>
              <div className="w-3 h-3 bg-pink-500 rounded-full animate-pulse delay-150"></div>
              <span className="text-gray-400 ml-2">Loading markets...</span>
            </div>
          </div>
        ) : markets.length === 0 ? (
          <div className="mb-8 relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-12">
              <div className="flex flex-col items-center gap-3">
                <svg
                  className="w-20 h-20 text-slate-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <p className="text-gray-400 text-lg font-semibold">
                  No {selectedSport} markets available
                </p>
                <p className="text-gray-500 text-sm">
                  Try selecting a different sport
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-8 relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
                <label className="block text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">
                  Select Market
                </label>
                <select
                  value={selectedTicker}
                  onChange={(e) => setSelectedTicker(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-xl px-4 py-3 text-white font-semibold focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                >
                  {markets.map((market) => (
                    <option key={market.ticker} value={market.ticker}>
                      {market.title} - {market.subtitle}
                    </option>
                  ))}
                </select>
                {selectedMarket && (
                  <div className="mt-3 flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-gray-400">
                      Showing data for:{' '}
                      <span className="text-white font-semibold">
                        {selectedMarket.ticker}
                      </span>
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Current Price Card */}
            {latestPrice && (
              <div className="mb-8 relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-green-600/50 to-blue-600/50 rounded-2xl blur opacity-20"></div>
                <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div>
                      <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">
                        Mid Price
                      </div>
                      <div className="text-3xl font-black text-white">
                        {latestPrice.mid_price.toFixed(1)}¢
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">
                        Bid / Ask
                      </div>
                      <div className="text-xl font-bold text-blue-400">
                        {latestPrice.yes_bid}¢ / {latestPrice.yes_ask}¢
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">
                        Spread
                      </div>
                      <div className="text-xl font-bold text-orange-400">
                        {latestPrice.spread.toFixed(1)}¢
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">
                        Volume
                      </div>
                      <div className="text-xl font-bold text-purple-400">
                        {latestPrice.volume.toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-between">
                    <div className="text-xs text-gray-500">
                      Last updated:{' '}
                      {format(
                        new Date(latestPrice.timestamp_ms),
                        'MMM d, h:mm:ss a'
                      )}
                    </div>
                    {priceLoading && (
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-blue-400">Updating...</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Chart Type Selector */}
            <div className="mb-6 flex gap-3">
              <button
                onClick={() => setChartType('line')}
                className={`px-6 py-3 rounded-xl font-bold transition-all ${
                  chartType === 'line'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50'
                    : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50'
                }`}
              >
                📈 Line Chart
              </button>
              <button
                onClick={() => setChartType('candle')}
                className={`px-6 py-3 rounded-xl font-bold transition-all ${
                  chartType === 'candle'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/50'
                    : 'bg-slate-800/50 text-gray-400 hover:bg-slate-700/50'
                }`}
              >
                🕯️ Candlestick Chart
              </button>
            </div>

            {/* Chart Container */}
            <div className="mb-8 relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <div className="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></div>
                    {chartType === 'line' ? 'Price History' : 'Candlestick Chart'}
                  </h2>
                </div>
                <div className="p-6">
                  {chartType === 'line' ? (
                    <LivePriceChart ticker={selectedTicker} />
                  ) : (
                    <LiveCandlestickChart ticker={selectedTicker} />
                  )}
                </div>
              </div>
            </div>

            {/* Trade History Table */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-pink-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
              <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <div className="w-1 h-6 bg-gradient-to-b from-pink-500 to-purple-500 rounded-full"></div>
                    Recent Trades
                  </h2>
                </div>
                <div className="p-6">
                  <TradeHistoryTable ticker={selectedTicker} />
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
