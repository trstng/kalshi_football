import { useEffect, useState } from 'react'
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { supabase, type MarketTick, type Game } from '../lib/supabase'
import { format } from 'date-fns'

type MarketChartProps = {
  game: Game
}

type ChartDataPoint = {
  timestamp: number
  time: string
  price: number
  pricePercent: number
}

export default function MarketChart({ game }: MarketChartProps) {
  const [ticks, setTicks] = useState<MarketTick[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMarketTicks()

    // Subscribe to new ticks for real-time updates
    const subscription = supabase
      .channel(`market_ticks_${game.market_ticker}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'market_ticks',
          filter: `market_ticker=eq.${game.market_ticker}`
        },
        () => {
          fetchMarketTicks()
        }
      )
      .subscribe()

    return () => {
      subscription.unsubscribe()
    }
  }, [game.market_ticker])

  async function fetchMarketTicks() {
    setLoading(true)
    const { data } = await supabase
      .from('market_ticks')
      .select('*')
      .eq('market_ticker', game.market_ticker)
      .order('timestamp', { ascending: true })

    if (data) {
      setTicks(data)
    }
    setLoading(false)
  }

  const chartData: ChartDataPoint[] = ticks.map(tick => ({
    timestamp: tick.timestamp,
    time: format(new Date(tick.timestamp * 1000), 'HH:mm:ss'),
    price: tick.favorite_price,
    pricePercent: tick.favorite_price * 100
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  if (ticks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p className="text-gray-400 text-lg">No market data yet</p>
        <p className="text-gray-500 text-sm">Price history will appear once monitoring begins</p>
      </div>
    )
  }

  const minPrice = Math.min(...chartData.map(d => d.pricePercent))
  const maxPrice = Math.max(...chartData.map(d => d.pricePercent))
  const yDomain = [Math.floor(minPrice - 5), Math.ceil(maxPrice + 5)]

  return (
    <div className="space-y-4">
      {/* Chart Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Current Price</div>
          <div className="text-2xl font-bold text-white">
            {(ticks[ticks.length - 1].favorite_price * 100).toFixed(1)}%
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">High</div>
          <div className="text-2xl font-bold text-green-400">
            {maxPrice.toFixed(1)}%
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Low</div>
          <div className="text-2xl font-bold text-red-400">
            {minPrice.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700/50">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              style={{ fontSize: '12px' }}
              tickFormatter={(value, index) => {
                // Show every 10th tick to avoid crowding
                return index % Math.ceil(chartData.length / 10) === 0 ? value : ''
              }}
            />
            <YAxis
              stroke="#94a3b8"
              style={{ fontSize: '12px' }}
              domain={yDomain}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '12px'
              }}
              labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: '4px' }}
              itemStyle={{ color: '#a78bfa', fontWeight: 'bold' }}
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Price']}
            />
            <Area
              type="monotone"
              dataKey="pricePercent"
              stroke="#a78bfa"
              strokeWidth={2}
              fill="url(#colorPrice)"
            />
            <Line
              type="monotone"
              dataKey="pricePercent"
              stroke="#a78bfa"
              strokeWidth={3}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Data Points Count */}
      <div className="text-center text-gray-500 text-sm">
        {ticks.length} data points • Updated every 10 seconds
      </div>
    </div>
  )
}
