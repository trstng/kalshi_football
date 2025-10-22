import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { fetchTrades, type Trade } from '../lib/liveChartApi'

interface TradeHistoryTableProps {
  ticker: string
}

export default function TradeHistoryTable({ ticker }: TradeHistoryTableProps) {
  const [trades, setTrades] = useState<Trade[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (ticker) {
      loadTrades()
      // Set up polling for updates
      const interval = setInterval(loadTrades, 10000) // Update every 10 seconds
      return () => clearInterval(interval)
    }
  }, [ticker])

  async function loadTrades() {
    setLoading(true)
    try {
      const data = await fetchTrades(ticker, 50)
      setTrades(data.trades)
    } catch (error) {
      console.error('Error loading trades:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading && trades.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
          <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse delay-75"></div>
          <div className="w-3 h-3 bg-pink-500 rounded-full animate-pulse delay-150"></div>
          <span className="text-gray-400 ml-2">Loading trades...</span>
        </div>
      </div>
    )
  }

  if (trades.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-slate-900/50 rounded-xl border border-slate-700/50">
        <div className="text-center">
          <svg
            className="w-16 h-16 text-slate-600 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <p className="text-gray-400 text-lg font-semibold">No trades yet</p>
          <p className="text-gray-500 text-sm mt-1">
            Trades will appear as they execute
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      {loading && (
        <div className="absolute top-0 right-0 flex items-center gap-2 px-3 py-1 bg-blue-500/20 rounded-lg">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-blue-400">Updating...</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="text-left py-3 px-4 text-gray-400 text-xs font-bold uppercase tracking-wider">
                Time
              </th>
              <th className="text-right py-3 px-4 text-gray-400 text-xs font-bold uppercase tracking-wider">
                Price
              </th>
              <th className="text-right py-3 px-4 text-gray-400 text-xs font-bold uppercase tracking-wider">
                Size
              </th>
              <th className="text-center py-3 px-4 text-gray-400 text-xs font-bold uppercase tracking-wider">
                Side
              </th>
              <th className="text-center py-3 px-4 text-gray-400 text-xs font-bold uppercase tracking-wider">
                Taker
              </th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, index) => (
              <tr
                key={trade.trade_id || index}
                className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
              >
                <td className="py-3 px-4 text-sm text-gray-300">
                  {format(new Date(trade.timestamp_ms), 'HH:mm:ss')}
                </td>
                <td className="py-3 px-4 text-right text-sm font-semibold text-white">
                  {trade.price}¢
                </td>
                <td className="py-3 px-4 text-right text-sm text-gray-400">
                  {trade.size.toLocaleString()}
                </td>
                <td className="py-3 px-4 text-center">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      trade.side === 'yes'
                        ? 'bg-blue-500/20 text-blue-400'
                        : 'bg-orange-500/20 text-orange-400'
                    }`}
                  >
                    {trade.side?.toUpperCase() || 'N/A'}
                  </span>
                </td>
                <td className="py-3 px-4 text-center">
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      trade.taker_side === 'buy'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {trade.taker_side?.toUpperCase() || 'N/A'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-center text-gray-500 text-sm">
        Showing {trades.length} most recent trades
      </div>
    </div>
  )
}
