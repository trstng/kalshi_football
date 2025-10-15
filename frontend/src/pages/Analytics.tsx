import { useEffect, useState } from 'react'
import { supabase, type BankrollHistory } from '../lib/supabase'
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'

export default function Analytics() {
  const [bankrollHistory, setBankrollHistory] = useState<BankrollHistory[]>([])

  useEffect(() => {
    fetchBankrollHistory()

    const subscription = supabase
      .channel('bankroll_updates')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'bankroll_history' }, fetchBankrollHistory)
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  async function fetchBankrollHistory() {
    const { data } = await supabase
      .from('bankroll_history')
      .select('*')
      .order('timestamp', { ascending: true })

    if (data) setBankrollHistory(data)
  }

  const chartData = bankrollHistory.map(item => ({
    time: format(new Date(item.timestamp * 1000), 'MMM d HH:mm'),
    bankroll: item.amount,
    change: item.change
  }))

  const currentBankroll = bankrollHistory.length > 0
    ? bankrollHistory[bankrollHistory.length - 1].amount
    : 500

  const totalPnL = currentBankroll - 500
  const totalReturn = ((currentBankroll - 500) / 500) * 100

  const maxBankroll = bankrollHistory.length > 0
    ? Math.max(...bankrollHistory.map(h => h.amount))
    : 500

  const minBankroll = bankrollHistory.length > 0
    ? Math.min(...bankrollHistory.map(h => h.amount))
    : 500

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Performance Analytics
          </h1>
          <p className="text-gray-400 text-lg">Real-time P&L tracking and bankroll visualization</p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Current Bankroll */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-blue-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Current Bankroll</span>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              </div>
              <div className="text-4xl font-black text-white">
                ${currentBankroll.toFixed(2)}
              </div>
              <div className="text-blue-400 text-sm font-semibold">
                Live Balance
              </div>
            </div>
          </div>

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
              <div className={`text-4xl font-black ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
              </div>
              <div className={`text-sm font-semibold ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(1)}% Return
              </div>
            </div>
          </div>

          {/* Peak Bankroll */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Peak</span>
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                ${maxBankroll.toFixed(2)}
              </div>
              <div className="text-purple-400 text-sm font-semibold">
                All-Time High
              </div>
            </div>
          </div>

          {/* Valley */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-amber-600 to-orange-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-amber-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Valley</span>
                <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                ${minBankroll.toFixed(2)}
              </div>
              <div className="text-amber-400 text-sm font-semibold">
                Lowest Point
              </div>
            </div>
          </div>
        </div>

        {/* Bankroll Chart */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                  Bankroll Over Time
                </h2>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"></div>
                  <span className="text-gray-400 font-semibold">Live Data</span>
                </div>
              </div>
            </div>
            <div className="p-6">
              {chartData.length === 0 ? (
                <div className="text-center py-16">
                  <div className="flex flex-col items-center gap-4">
                    <svg className="w-20 h-20 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <div>
                      <p className="text-gray-400 text-xl font-semibold mb-1">No data yet</p>
                      <p className="text-gray-500 text-sm">Chart will populate after first trade completes</p>
                    </div>
                  </div>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorBankroll" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      style={{ fontSize: '12px', fontWeight: 600 }}
                      tick={{ fill: '#94a3b8' }}
                    />
                    <YAxis
                      stroke="#64748b"
                      style={{ fontSize: '12px', fontWeight: 600 }}
                      tick={{ fill: '#94a3b8' }}
                      domain={['dataMin - 10', 'dataMax + 10']}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '12px',
                        padding: '12px',
                        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)'
                      }}
                      labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
                      itemStyle={{ color: '#ffffff', fontWeight: 'bold' }}
                      formatter={(value: number) => [`$${value.toFixed(2)}`, 'Bankroll']}
                    />
                    <Area
                      type="monotone"
                      dataKey="bankroll"
                      stroke="url(#gradient)"
                      strokeWidth={3}
                      fill="url(#colorBankroll)"
                      dot={false}
                      activeDot={{
                        r: 6,
                        fill: '#3b82f6',
                        stroke: '#1e293b',
                        strokeWidth: 2
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="bankroll"
                      stroke="url(#gradient)"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{
                        r: 6,
                        fill: '#3b82f6',
                        stroke: '#1e293b',
                        strokeWidth: 2
                      }}
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#3b82f6" />
                        <stop offset="50%" stopColor="#8b5cf6" />
                        <stop offset="100%" stopColor="#ec4899" />
                      </linearGradient>
                    </defs>
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
