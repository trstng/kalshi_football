import { useEffect, useState, useMemo } from 'react'
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, Legend } from 'recharts'
import { supabase, type MarketTick, type Game } from '../lib/supabase'
import { format } from 'date-fns'

type MarketChartProps = {
  game: Game
}

type CandlestickData = {
  timestamp: number
  time: string
  open: number
  high: number
  low: number
  close: number
  yesAskOpen: number
  yesAskClose: number
  noAskOpen: number
  noAskClose: number
}

// Custom candlestick shape component
const Candlestick = (props: any) => {
  const { x, y, width, height, open, close, high, low, fill } = props
  const isGreen = close > open
  const color = isGreen ? '#10b981' : '#ef4444'
  const bodyHeight = Math.abs(close - open) || 1
  const bodyY = Math.min(y + (isGreen ? (high - close) : (high - open)), y + height - 1)

  return (
    <g>
      {/* High-Low wick */}
      <line
        x1={x + width / 2}
        y1={y}
        x2={x + width / 2}
        y2={y + height}
        stroke={color}
        strokeWidth={1}
      />
      {/* Open-Close body */}
      <rect
        x={x}
        y={bodyY}
        width={width}
        height={bodyHeight}
        fill={color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  )
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

  // Aggregate ticks into 1-minute candlesticks for better visualization
  const chartData: CandlestickData[] = useMemo(() => {
    if (ticks.length === 0) return []

    // Group by 1-minute buckets
    const buckets = new Map<number, MarketTick[]>()

    ticks.forEach(tick => {
      const bucketTime = Math.floor(tick.timestamp / 60) * 60 // Round to minute
      if (!buckets.has(bucketTime)) {
        buckets.set(bucketTime, [])
      }
      buckets.get(bucketTime)!.push(tick)
    })

    // Create candlestick data
    return Array.from(buckets.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([timestamp, ticksInBucket]) => {
        const prices = ticksInBucket.map(t => t.favorite_price * 100)
        const yesAsks = ticksInBucket.map(t => t.yes_ask || 0)
        const noAsks = ticksInBucket.map(t => t.no_ask || 0)

        return {
          timestamp,
          time: format(new Date(timestamp * 1000), 'HH:mm'),
          open: prices[0],
          high: Math.max(...prices),
          low: Math.min(...prices),
          close: prices[prices.length - 1],
          yesAskOpen: yesAsks[0],
          yesAskClose: yesAsks[yesAsks.length - 1],
          noAskOpen: noAsks[0],
          noAskClose: noAsks[noAsks.length - 1],
        }
      })
  }, [ticks])

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

  const minPrice = chartData.length > 0 ? Math.min(...chartData.map(d => d.low)) : 0
  const maxPrice = chartData.length > 0 ? Math.max(...chartData.map(d => d.high)) : 100
  const currentPrice = chartData.length > 0 ? chartData[chartData.length - 1].close : 0
  const yDomain = [Math.max(0, Math.floor(minPrice - 5)), Math.min(100, Math.ceil(maxPrice + 5))]

  return (
    <div className="space-y-4">
      {/* Chart Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Current</div>
          <div className="text-2xl font-bold text-white">
            {currentPrice.toFixed(1)}%
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
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Candles</div>
          <div className="text-2xl font-bold text-purple-400">
            {chartData.length}
          </div>
          <div className="text-xs text-gray-500 mt-1">{ticks.length} raw ticks</div>
        </div>
      </div>

      {/* Candlestick Chart */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700/50">
        <ResponsiveContainer width="100%" height={500}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis
              dataKey="time"
              stroke="#94a3b8"
              style={{ fontSize: '11px' }}
              interval="preserveStartEnd"
              tickFormatter={(value, index) => {
                // Show every nth tick based on data length
                const interval = Math.max(1, Math.floor(chartData.length / 15))
                return index % interval === 0 ? value : ''
              }}
            />
            <YAxis
              stroke="#94a3b8"
              style={{ fontSize: '11px' }}
              domain={yDomain}
              tickFormatter={(value) => `${value}%`}
            />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              iconType="line"
              formatter={(value) => {
                if (value === 'yesAskClose') return 'Yes Ask'
                if (value === 'noAskClose') return 'No Ask'
                return value
              }}
            />
            <Tooltip
              content={(props: any) => {
                if (!props.active || !props.payload || !props.payload[0]) return null
                const data = props.payload[0].payload
                const isUp = data.close >= data.open
                return (
                  <div className="bg-slate-900/95 border border-slate-700 rounded-lg p-3 shadow-xl">
                    <div className="text-gray-400 text-xs font-bold mb-2">{data.time}</div>
                    <div className="space-y-1 text-sm">
                      <div className="text-gray-400 text-xs font-semibold uppercase mb-1">Favorite Price</div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-500">Open:</span>
                        <span className="text-white font-semibold">{data.open.toFixed(2)}%</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-500">High:</span>
                        <span className="text-green-400 font-semibold">{data.high.toFixed(2)}%</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-500">Low:</span>
                        <span className="text-red-400 font-semibold">{data.low.toFixed(2)}%</span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-gray-500">Close:</span>
                        <span className={`font-semibold ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                          {data.close.toFixed(2)}%
                        </span>
                      </div>
                      <div className="border-t border-slate-700 mt-2 pt-2">
                        <div className="flex justify-between gap-4">
                          <span className="text-blue-400">Yes Ask:</span>
                          <span className="text-blue-300 font-semibold">{data.yesAskClose.toFixed(2)}¢</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-amber-400">No Ask:</span>
                          <span className="text-amber-300 font-semibold">{data.noAskClose.toFixed(2)}¢</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )
              }}
            />
            {/* Render candlesticks using custom shape */}
            <Bar
              dataKey="high"
              fill="transparent"
              shape={(props: any) => {
                const data = chartData[props.index]
                if (!data) return null

                const { x, y, width, height } = props
                const isGreen = data.close >= data.open
                const color = isGreen ? '#10b981' : '#ef4444'

                // Calculate pixel positions for price levels
                const highY = y
                const lowY = y + height
                const openY = y + ((data.high - data.open) / (data.high - data.low)) * height
                const closeY = y + ((data.high - data.close) / (data.high - data.low)) * height

                const bodyTop = Math.min(openY, closeY)
                const bodyHeight = Math.max(Math.abs(closeY - openY), 2)

                return (
                  <g key={`candle-${props.index}`}>
                    {/* High-Low wick */}
                    <line
                      x1={x + width / 2}
                      y1={highY}
                      x2={x + width / 2}
                      y2={lowY}
                      stroke={color}
                      strokeWidth={1.5}
                      opacity={0.5}
                    />
                    {/* Open-Close body */}
                    <rect
                      x={x + 2}
                      y={bodyTop}
                      width={Math.max(width - 4, 4)}
                      height={bodyHeight}
                      fill={color}
                      stroke={color}
                      strokeWidth={1}
                      opacity={0.5}
                    />
                  </g>
                )
              }}
            />
            {/* Yes Ask Line */}
            <Line
              type="monotone"
              dataKey="yesAskClose"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Yes Ask"
            />
            {/* No Ask Line */}
            <Line
              type="monotone"
              dataKey="noAskClose"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
              name="No Ask"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Data Info */}
      <div className="text-center text-gray-500 text-sm">
        Candlesticks show Favorite Price (OHLC) • Lines show Yes Ask (blue) & No Ask (orange) • 1-minute intervals • {ticks.length} raw ticks
      </div>
    </div>
  )
}
