import { useEffect, useState } from 'react'
import ReactApexChart from 'react-apexcharts'
import type { ApexOptions } from 'apexcharts'
import { fetchPriceHistory, type PriceHistory } from '../lib/liveChartApi'

interface LivePriceChartProps {
  ticker: string
}

export default function LivePriceChart({ ticker }: LivePriceChartProps) {
  const [chartData, setChartData] = useState<PriceHistory | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | 'all'>('6h')

  useEffect(() => {
    if (ticker) {
      loadChartData()
      // Set up polling for updates
      const interval = setInterval(loadChartData, 5000) // Update every 5 seconds
      return () => clearInterval(interval)
    }
  }, [ticker, timeRange])

  async function loadChartData() {
    setLoading(true)
    try {
      let options: { start_time?: number; limit?: number } = { limit: 2000 }

      if (timeRange !== 'all') {
        const now = Math.floor(Date.now() / 1000)
        const hours = timeRange === '1h' ? 1 : timeRange === '6h' ? 6 : 24
        options.start_time = now - hours * 3600
      }

      const data = await fetchPriceHistory(ticker, options)
      setChartData(data)
    } catch (error) {
      console.error('Error loading chart data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !chartData) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <div className="flex flex-col items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="w-4 h-4 bg-purple-500 rounded-full animate-pulse delay-75"></div>
            <div className="w-4 h-4 bg-pink-500 rounded-full animate-pulse delay-150"></div>
          </div>
          <span className="text-gray-400 text-lg font-semibold">
            Loading chart data...
          </span>
        </div>
      </div>
    )
  }

  if (!chartData || chartData.series.length === 0) {
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
            No price data available
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
      type: 'line',
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
        enabled: true,
        dynamicAnimation: {
          enabled: true,
          speed: 1000,
        },
      },
    },
    theme: {
      mode: 'dark',
    },
    stroke: {
      curve: 'smooth',
      width: 3,
    },
    colors: ['#00E396', '#008FFB', '#FEB019'],
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
          show: true,
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
      x: {
        format: 'MMM dd, h:mm:ss TT',
      },
      y: {
        formatter: (value) => `${value?.toFixed(2)}¢`,
      },
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'left',
      labels: {
        colors: '#94a3b8',
      },
    },
  }

  return (
    <div className="w-full">
      {/* Time Range Selector */}
      <div className="mb-6 flex gap-3">
        {(['1h', '6h', '24h', 'all'] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              timeRange === range
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/50'
                : 'bg-slate-700/50 text-gray-400 hover:bg-slate-600/50'
            }`}
          >
            {range === 'all' ? 'All' : range.toUpperCase()}
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
            Data Points
          </div>
          <div className="text-2xl font-bold text-white">{chartData.count}</div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
            Time Range
          </div>
          <div className="text-2xl font-bold text-purple-400">
            {timeRange === 'all' ? 'All Time' : timeRange.toUpperCase()}
          </div>
        </div>
        <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
          <div className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-1">
            Series
          </div>
          <div className="text-2xl font-bold text-blue-400">
            {chartData.series.length}
          </div>
        </div>
      </div>

      {/* ApexChart */}
      <div className="bg-slate-900/50 rounded-xl border border-slate-700/50 p-4">
        <ReactApexChart
          options={options}
          series={chartData.series}
          type="line"
          height={600}
        />
      </div>

      {/* Legend Info */}
      <div className="mt-4 text-center text-gray-500 text-sm">
        <span className="text-green-400 font-semibold">Mid Price</span> •{' '}
        <span className="text-blue-400 font-semibold">Yes Bid</span> •{' '}
        <span className="text-orange-400 font-semibold">Yes Ask</span>
      </div>
    </div>
  )
}
