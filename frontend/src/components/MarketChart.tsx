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

    // Only fetch ticks from kickoff onwards (in-game data only)
    const { data } = await supabase
      .from('market_ticks')
      .select('*')
      .eq('market_ticker', game.market_ticker)
      .gte('timestamp', game.kickoff_ts)
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

  // Check if game has kicked off
  const now = Math.floor(Date.now() / 1000)
  const hasKickedOff = now >= game.kickoff_ts
  const timeToKickoff = game.kickoff_ts - now

  // Pregame view: Show checkpoint system
  if (!hasKickedOff) {
    const checkpoints = [
      { label: '6 Hours', odds: game.odds_6h, timestamp: game.checkpoint_6h_ts },
      { label: '3 Hours', odds: game.odds_3h, timestamp: game.checkpoint_3h_ts },
      { label: '30 Minutes', odds: game.odds_30m, timestamp: game.checkpoint_30m_ts }
    ]

    const hoursUntilKickoff = Math.floor(timeToKickoff / 3600)
    const minutesUntilKickoff = Math.floor((timeToKickoff % 3600) / 60)

    return (
      <div className="space-y-6">
        {/* Pregame Status */}
        <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Pregame Monitoring</h3>
              <p className="text-gray-400 text-sm">
                Kickoff in {hoursUntilKickoff}h {minutesUntilKickoff}m • Checking eligibility
              </p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
              <span className="text-blue-400 text-sm font-semibold">Monitoring</span>
            </div>
          </div>

          {/* Checkpoint Grid */}
          <div className="grid grid-cols-3 gap-4">
            {checkpoints.map((checkpoint, idx) => (
              <div
                key={idx}
                className={`rounded-lg p-4 border transition-all ${
                  checkpoint.odds !== null
                    ? 'bg-slate-700/50 border-slate-600'
                    : 'bg-slate-800/30 border-slate-700/30 opacity-50'
                }`}
              >
                <div className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-2">
                  {checkpoint.label}
                </div>
                {checkpoint.odds !== null ? (
                  <>
                    <div className={`text-3xl font-bold mb-1 ${
                      checkpoint.odds >= 0.57 ? 'text-green-400' : 'text-gray-300'
                    }`}>
                      {(checkpoint.odds * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {checkpoint.timestamp && format(new Date(checkpoint.timestamp * 1000), 'HH:mm:ss')}
                    </div>
                  </>
                ) : (
                  <div className="text-2xl text-gray-600">—</div>
                )}
              </div>
            ))}
          </div>

          {/* Eligibility Status */}
          {game.is_eligible !== null && (
            <div className={`mt-4 p-4 rounded-lg border ${
              game.is_eligible
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-center gap-2">
                {game.is_eligible ? (
                  <>
                    <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-green-400 font-semibold">Eligible for Trading</span>
                    <span className="text-gray-400 text-sm ml-auto">Orders will be placed if odds drop below 50%</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <span className="text-red-400 font-semibold">Not Eligible</span>
                    <span className="text-gray-400 text-sm ml-auto">No checkpoint reached 57% threshold</span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/30">
          <p className="text-gray-400 text-sm">
            <span className="font-semibold text-white">Pregame Monitoring:</span> The bot checks odds at 3 key checkpoints (6h, 3h, 30m before kickoff) to determine if this game qualifies for trading. In-game price streaming will begin after kickoff for visualization and backtesting data.
          </p>
        </div>
      </div>
    )
  }

  // In-game: No ticks yet
  if (ticks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-3">
        <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p className="text-gray-400 text-lg">Game Started - Waiting for price data</p>
        <p className="text-gray-500 text-sm">In-game price ticks will appear shortly</p>
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
                if (!data) return <g />

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
