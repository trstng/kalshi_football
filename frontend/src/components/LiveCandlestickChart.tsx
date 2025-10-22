import { useEffect, useState } from 'react'
import ReactApexChart from 'react-apexcharts'
import type { ApexOptions } from 'apexcharts'
import { fetchCandles, type CandleData } from '../lib/liveChartApi'

interface LiveCandlestickChartProps {
  ticker: string
}

export default function LiveCandlestickChart({ ticker }: LiveCandlestickChartProps) {
  const [candleData, setCandleData] = useState<CandleData | null>(null)
  const [loading, setLoading] = useState(true)
  const [candleInterval, setCandleInterval] = useState<'1m' | '5m' | '15m' | '1h'>('5m')

  useEffect(() => {
    if (ticker) {
      loadCandleData()
      // Set up polling for updates
      const pollingInterval = setInterval(loadCandleData, 10000) // Update every 10 seconds
      return () => clearInterval(pollingInterval)
    }
  }, [ticker, candleInterval])

  async function loadCandleData() {
    setLoading(true)
    try {
      const data = await fetchCandles(ticker, { interval: candleInterval, limit: 500 })
      setCandleData(data)
    } catch (error) {
      console.error('Error loading candle data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !candleData) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse delay-75"></div>
            <div className="w-4 h-4 bg-pink-500 rounded-full animate-pulse delay-150"></div>
          </div>
          <span className="text-gray-400 text-lg font-semibold">
            Loading candlestick data...
          </span>
        </div>
      </div>
    )
  }

  if (!candleData || candleData.candles.length === 0) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-slate-900/50 rounded-xl border border-slate-700/50">
        <div className="text-center">
          <svg
            className="w-20 h-20 text-slate-600 mx-auto mb-4"
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
            No candlestick data available
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Data will appear once the market starts streaming
          </p>
        </div>
      </div>
    )
  }

  const options: ApexOptions = {
    chart: {
      type: 'candlestick',
      background: 'transparent',
      toolbar: {
        show: true,
        tools: {
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true,
        },
      },
      zoom: {
        enabled: true,
        type: 'x',
        autoScaleYaxis: true,
      },
      animations: {
        enabled: false, // Disable animations for better performance with candlesticks
      },
    },
    theme: {
      mode: 'dark',
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#10b981',
          downward: '#ef4444',
        },
        wick: {
          useFillColor: true,
        },
      },
    },
    xaxis: {
      type: 'datetime',
      labels: {
        style: {
          colors: '#94a3b8',
          fontSize: '12px',
          fontWeight: 600,
        },
        datetimeFormatter: {
          hour: 'h:mm TT',
          minute: 'h:mm TT',
        },
      },
    },
    yaxis: {
      title: {
        text: 'Price (¢)',
        style: {
          color: '#94a3b8',
          fontSize: '14px',
          fontWeight: 600,
        },
      },
      min: 0,
      max: 100,
      tooltip: {
        enabled: true,
      },
      labels: {
        style: {
          colors: '#94a3b8',
          fontSize: '12px',
          fontWeight: 600,
        },
        formatter: (value) => `${value}¢`,
      },
    },
    grid: {
      borderColor: '#334155',
      strokeDashArray: 3,
      xaxis: {
        lines: {
          show: false,
        },
      },
      yaxis: {
        lines: {
          show: true,
        },
      },
    },
    tooltip: {
      theme: 'dark',
      custom: function ({ dataPointIndex }: any) {
        const candle = candleData.candles[dataPointIndex]
        if (!candle) return ''

        const [open, high, low, close] = candle.y
        const isUp = close >= open

        return `
          <div class="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg p-4 shadow-2xl">
            <div class="text-gray-400 text-xs font-semibold mb-2">
              ${new Date(candle.x).toLocaleString()}
            </div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1">
              <div class="text-gray-500 text-xs">Open:</div>
              <div class="text-white text-xs font-bold">${open.toFixed(1)}¢</div>
              <div class="text-gray-500 text-xs">High:</div>
              <div class="text-green-400 text-xs font-bold">${high.toFixed(1)}¢</div>
              <div class="text-gray-500 text-xs">Low:</div>
              <div class="text-red-400 text-xs font-bold">${low.toFixed(1)}¢</div>
              <div class="text-gray-500 text-xs">Close:</div>
              <div class="text-${isUp ? 'green' : 'red'}-400 text-xs font-bold">${close.toFixed(1)}¢</div>
            </div>
          </div>
        `
      },
    },
  }

  const series = [
    {
      name: 'Price',
      data: candleData.candles,
    },
  ]

  return (
    <div className="w-full">
      {/* Interval Selector */}
      <div className="mb-6 flex gap-3">
        {(['1m', '5m', '15m', '1h'] as const).map((int) => (
          <button
            key={int}
            onClick={() => setCandleInterval(int)}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              candleInterval === int
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
                : 'bg-slate-700/50 text-gray-400 hover:bg-slate-600/50'
            }`}
          >
            {int === '1m'
              ? '1 Minute'
              : int === '5m'
              ? '5 Minutes'
              : int === '15m'
              ? '15 Minutes'
              : '1 Hour'}
          </button>
        ))}
        {loading && (
          <div className="ml-auto flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-blue-400">Updating...</span>
          </div>
        )}
      </div>

      {/* Chart Stats */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
            Candles
          </div>
          <div className="text-2xl font-bold text-white">{candleData.count}</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
            Interval
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {candleInterval === '1m'
              ? '1m'
              : candleInterval === '5m'
              ? '5m'
              : candleInterval === '15m'
              ? '15m'
              : '1h'}
          </div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
            Latest Close
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {candleData.candles.length > 0
              ? `${candleData.candles[candleData.candles.length - 1].y[3].toFixed(1)}¢`
              : 'N/A'}
          </div>
        </div>
      </div>

      {/* ApexChart */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-700/50 p-4">
        <ReactApexChart
          options={options}
          series={series}
          type="candlestick"
          height={600}
        />
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-4 h-6 bg-green-500 border border-green-600 rounded-sm"></div>
          <span className="text-gray-400 text-sm font-semibold">
            Bullish Candle
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-6 bg-red-500 border border-red-600 rounded-sm"></div>
          <span className="text-gray-400 text-sm font-semibold">
            Bearish Candle
          </span>
        </div>
      </div>
    </div>
  )
}
