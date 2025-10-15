import { useEffect, useState } from 'react'
import { supabase, type Game, type Position, type Order } from '../lib/supabase'
import { format } from 'date-fns'

export default function Dashboard() {
  const [activeGames, setActiveGames] = useState<Game[]>([])
  const [openOrders, setOpenOrders] = useState<Order[]>([])
  const [openPositions, setOpenPositions] = useState<Position[]>([])
  const [currentBankroll, setCurrentBankroll] = useState(500)

  useEffect(() => {
    fetchActiveGames()
    fetchOpenOrders()
    fetchOpenPositions()
    fetchBankroll()

    const gamesSubscription = supabase
      .channel('games_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'games' }, fetchActiveGames)
      .subscribe()

    const ordersSubscription = supabase
      .channel('orders_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'orders' }, fetchOpenOrders)
      .subscribe()

    const positionsSubscription = supabase
      .channel('positions_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'positions' }, fetchOpenPositions)
      .subscribe()

    const bankrollSubscription = supabase
      .channel('bankroll_changes')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'bankroll_history' }, fetchBankroll)
      .subscribe()

    return () => {
      gamesSubscription.unsubscribe()
      ordersSubscription.unsubscribe()
      positionsSubscription.unsubscribe()
      bankrollSubscription.unsubscribe()
    }
  }, [])

  async function fetchActiveGames() {
    const { data } = await supabase
      .from('games')
      .select('*')
      .in('status', ['monitoring', 'triggered'])
      .order('kickoff_ts', { ascending: true })
    if (data) setActiveGames(data)
  }

  async function fetchOpenOrders() {
    const { data } = await supabase
      .from('orders')
      .select('*')
      .eq('status', 'pending')
      .order('created_at', { ascending: false })
    if (data) setOpenOrders(data)
  }

  async function fetchOpenPositions() {
    const { data } = await supabase
      .from('positions')
      .select('*')
      .eq('status', 'open')
      .order('entry_time', { ascending: false })
    if (data) setOpenPositions(data)
  }

  async function fetchBankroll() {
    const { data } = await supabase
      .from('bankroll_history')
      .select('amount')
      .order('timestamp', { ascending: false })
      .limit(1)
    if (data && data.length > 0) {
      setCurrentBankroll(data[0].amount)
    }
  }

  const totalExposure = openPositions.reduce((sum, pos) => sum + (pos.entry_price * pos.size / 100), 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Live Trading Dashboard
          </h1>
          <p className="text-gray-400 text-lg">Real-time market monitoring and position tracking</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Bankroll Card */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-green-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Bankroll</span>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              </div>
              <div className="text-4xl font-black text-white mb-1">
                ${currentBankroll.toFixed(2)}
              </div>
              <div className="text-green-400 text-sm font-semibold">
                +{((currentBankroll - 500) / 500 * 100).toFixed(1)}% ROI
              </div>
            </div>
          </div>

          {/* Active Games Card */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-blue-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Active Games</span>
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                {activeGames.length}
              </div>
              <div className="text-blue-400 text-sm font-semibold">
                Being Monitored
              </div>
            </div>
          </div>

          {/* Open Orders Card */}
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-30 group-hover:opacity-100 transition duration-300"></div>
            <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 border border-purple-500/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm font-semibold uppercase tracking-wider">Open Orders</span>
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div className="text-4xl font-black text-white">
                {openOrders.length}
              </div>
              <div className="text-purple-400 text-sm font-semibold">
                {openPositions.length} Filled
              </div>
            </div>
          </div>
        </div>

        {/* Active Games Table */}
        <div className="mb-8 relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                Active Games
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Game
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Kickoff
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Checkpoint Odds
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Eligibility
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {activeGames.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <p className="text-gray-400 text-lg">No active games</p>
                          <p className="text-gray-500 text-sm">The bot will discover games automatically</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    activeGames.map((game) => (
                      <tr key={game.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-white text-lg">{game.market_title}</div>
                          <div className="text-gray-500 text-sm">{game.yes_subtitle}</div>
                        </td>
                        <td className="px-6 py-4 text-gray-300 font-medium">
                          {format(new Date(game.kickoff_ts * 1000), 'MMM d, h:mm a')}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1.5">
                            {/* 6h checkpoint */}
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 text-xs font-semibold w-8">6h:</span>
                              {game.odds_6h ? (
                                <div className="inline-flex items-center gap-2 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/30">
                                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full"></div>
                                  <span className="text-blue-300 font-bold text-sm">{(game.odds_6h * 100).toFixed(0)}%</span>
                                  {game.checkpoint_6h_ts && (
                                    <span className="text-gray-500 text-xs">
                                      {format(new Date(game.checkpoint_6h_ts * 1000), 'h:mm a')}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-gray-600 text-xs">Pending</span>
                              )}
                            </div>
                            {/* 3h checkpoint */}
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 text-xs font-semibold w-8">3h:</span>
                              {game.odds_3h ? (
                                <div className="inline-flex items-center gap-2 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/30">
                                  <div className="w-1.5 h-1.5 bg-purple-400 rounded-full"></div>
                                  <span className="text-purple-300 font-bold text-sm">{(game.odds_3h * 100).toFixed(0)}%</span>
                                  {game.checkpoint_3h_ts && (
                                    <span className="text-gray-500 text-xs">
                                      {format(new Date(game.checkpoint_3h_ts * 1000), 'h:mm a')}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-gray-600 text-xs">Pending</span>
                              )}
                            </div>
                            {/* 30m checkpoint */}
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500 text-xs font-semibold w-8">30m:</span>
                              {game.odds_30m ? (
                                <div className="inline-flex items-center gap-2 bg-green-500/10 px-2 py-0.5 rounded border border-green-500/30">
                                  <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                                  <span className="text-green-300 font-bold text-sm">{(game.odds_30m * 100).toFixed(0)}%</span>
                                  {game.checkpoint_30m_ts && (
                                    <span className="text-gray-500 text-xs">
                                      {format(new Date(game.checkpoint_30m_ts * 1000), 'h:mm a')}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-gray-600 text-xs">Pending</span>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {game.is_eligible === null ? (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-gray-500/20 text-gray-400 border border-gray-500/50">
                              Pending
                            </span>
                          ) : game.is_eligible ? (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-green-500/20 text-green-400 border border-green-500/50">
                              ✓ Eligible
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-red-500/20 text-red-400 border border-red-500/50">
                              ✗ Not Eligible
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                            game.status === 'triggered'
                              ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                              : 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                          }`}>
                            {game.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Open Orders Table */}
        <div className="mb-8 relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-orange-600/50 to-amber-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <div className="w-1 h-6 bg-gradient-to-b from-orange-500 to-amber-500 rounded-full"></div>
                Open Orders (Limit Order Ladder)
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
                      Limit Price
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Filled
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Time Placed
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {openOrders.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          <p className="text-gray-400 text-lg">No pending orders</p>
                          <p className="text-gray-500 text-sm">Orders will appear here once game becomes eligible</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    openOrders.map((order) => (
                      <tr key={order.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-white text-sm">{order.market_ticker}</div>
                          <div className="text-gray-500 text-xs font-mono">{order.order_id.slice(0, 8)}...</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="inline-flex items-center gap-2 bg-orange-500/20 px-3 py-1 rounded-full border border-orange-500/50">
                            <span className="text-orange-300 font-bold">{order.price}¢</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300 font-bold">
                          {order.size} contracts
                        </td>
                        <td className="px-6 py-4">
                          {order.filled_size > 0 ? (
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-700 rounded-full h-2 overflow-hidden">
                                <div
                                  className="bg-gradient-to-r from-green-500 to-emerald-500 h-full transition-all"
                                  style={{ width: `${(order.filled_size / order.size) * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-green-400 font-bold text-sm">
                                {order.filled_size}/{order.size}
                              </span>
                            </div>
                          ) : (
                            <span className="text-gray-500 text-sm">0/{order.size}</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                            order.status === 'pending'
                              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'
                              : 'bg-green-500/20 text-green-400 border border-green-500/50'
                          }`}>
                            {order.status === 'pending' ? '⏳ Pending' : order.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-400 font-medium text-sm">
                          {format(new Date(order.created_at), 'MMM d, h:mm a')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Open Positions Table */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-600/50 to-pink-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
                Open Positions
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
                      Entry Price
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Entry Time
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {openPositions.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-12 text-center">
                        <div className="flex flex-col items-center gap-3">
                          <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <p className="text-gray-400 text-lg">No open positions</p>
                          <p className="text-gray-500 text-sm">Waiting for entry signals</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    openPositions.map((position) => (
                      <tr key={position.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                        <td className="px-6 py-4 font-bold text-white text-lg">
                          {position.market_ticker}
                        </td>
                        <td className="px-6 py-4">
                          <div className="inline-flex items-center gap-2 bg-emerald-500/20 px-3 py-1 rounded-full border border-emerald-500/50">
                            <span className="text-emerald-400 font-bold">{position.entry_price}¢</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-gray-300 font-bold">
                          {position.size} contracts
                        </td>
                        <td className="px-6 py-4 text-gray-400 font-medium">
                          {format(new Date(position.entry_time * 1000), 'MMM d, h:mm a')}
                        </td>
                      </tr>
                    ))
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
