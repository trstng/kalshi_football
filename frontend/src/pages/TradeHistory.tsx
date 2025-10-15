import { useEffect, useState } from 'react'
import { supabase, type Position } from '../lib/supabase'
import { format } from 'date-fns'

export default function TradeHistory() {
  const [closedPositions, setClosedPositions] = useState<Position[]>([])

  useEffect(() => {
    fetchClosedPositions()

    const subscription = supabase
      .channel('closed_positions')
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'positions',
        filter: 'status=eq.closed'
      }, fetchClosedPositions)
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  async function fetchClosedPositions() {
    const { data } = await supabase
      .from('positions')
      .select('*')
      .eq('status', 'closed')
      .order('exit_time', { ascending: false })
      .limit(100)

    if (data) setClosedPositions(data)
  }

  const totalPnL = closedPositions.reduce((sum, pos) => sum + (pos.pnl || 0), 0)
  const winningTrades = closedPositions.filter(p => (p.pnl || 0) > 0).length
  const winRate = closedPositions.length > 0 ? (winningTrades / closedPositions.length) * 100 : 0
  const avgWin = winningTrades > 0
    ? closedPositions.filter(p => (p.pnl || 0) > 0).reduce((sum, p) => sum + (p.pnl || 0), 0) / winningTrades
    : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Trade History
          </h1>
          <p className="text-gray-400 text-lg">Complete performance breakdown and trade log</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Total P&L */}
          <div className="relative group">
            <div className={`absolute -inset-0.5 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300 ${
              totalPnL >= 0 ? 'bg-gradient-to-r from-green-600 to-emerald-600' : 'bg-gradient-to-r from-red-600 to-rose-600'
            }`}></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Total P&L</span>
                <svg className={`w-5 h-5 ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={totalPnL >= 0 ? "M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" : "M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"} />
                </svg>
              </div>
              <div className={`text-4xl font-black mb-1 ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
              </div>
              <div className="text-gray-400 text-sm font-semibold">
                All-Time Returns
              </div>
            </div>
          </div>

          {/* Total Trades */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-blue-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Total Trades</span>
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                {closedPositions.length}
              </div>
              <div className="text-blue-400 text-sm font-semibold">
                Completed Positions
              </div>
            </div>
          </div>

          {/* Win Rate */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Win Rate</span>
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                {winRate.toFixed(1)}%
              </div>
              <div className="text-purple-400 text-sm font-semibold">
                {winningTrades}W / {closedPositions.length - winningTrades}L
              </div>
            </div>
          </div>

          {/* Avg Win */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-600 to-orange-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-amber-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Avg Win</span>
                <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                ${avgWin.toFixed(2)}
              </div>
              <div className="text-amber-400 text-sm font-semibold">
                Per Winning Trade
              </div>
            </div>
          </div>
        </div>

        {/* Closed Positions Table */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                Closed Positions
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Market
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Entry
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Exit
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      P&L
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Exit Time
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {closedPositions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          <p className="text-gray-400 text-lg">No closed positions yet</p>
                          <p className="text-gray-500 text-sm">Trades will appear here after exits</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    closedPositions.map((position) => {
                      const pnl = position.pnl || 0
                      const isWin = pnl > 0
                      return (
                        <tr key={position.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                          <td className="px-6 py-4">
                            <div className="font-bold text-white text-lg">{position.market_ticker}</div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-300 font-medium">{position.entry_price}¢</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-300 font-medium">{position.exit_price}¢</span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-gray-400 font-medium">{position.size}</span>
                          </td>
                          <td className="px-6 py-4">
                            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full font-black ${
                              isWin
                                ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                                : 'bg-red-500/20 text-red-400 border border-red-500/50'
                            }`}>
                              {isWin && '+'}${pnl.toFixed(2)}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-gray-400 font-medium">
                            {position.exit_time && format(new Date(position.exit_time * 1000), 'MMM d, h:mm a')}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
