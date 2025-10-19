import ReactApexChart from 'react-apexcharts'
import type { ApexOptions } from 'apexcharts'
import { format } from 'date-fns'
import type { Candle, TradeMarker } from '../lib/chartHelpers'

interface CandlestickChartProps {
  candles: Candle[]
  markers: TradeMarker[]
}

export default function CandlestickChart({ candles, markers }: CandlestickChartProps) {
  if (candles.length === 0) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-slate-900/50 rounded-xl border border-slate-700/50">
        <div className="text-center">
          <svg className="w-20 h-20 text-slate-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-400 text-lg font-semibold">No chart data available</p>
          <p className="text-gray-500 text-sm mt-2">Select a game with tick data</p>
        </div>
      </div>
    )
  }

  console.log('Rendering candlestick chart with', candles.length, 'candles')

  // Transform candles to ApexCharts format: [[timestamp, [open, high, low, close]]]
  const series = [{
    name: 'Price',
    data: candles.map(candle => ({
      x: new Date(candle.timestamp * 1000),
      y: [candle.open, candle.high, candle.low, candle.close]
    }))
  }]

  // Add marker annotations
  const annotations: any = {
    points: [
      ...markers.filter(m => m.type === 'entry').map(m => ({
        x: new Date(m.timestamp * 1000).getTime(),
        y: m.price,
        marker: {
          size: 8,
          fillColor: '#3b82f6',
          strokeColor: '#1d4ed8',
          strokeWidth: 2,
        },
        label: {
          borderColor: '#3b82f6',
          style: {
            color: '#fff',
            background: '#3b82f6',
          },
          text: `Entry ${m.price}¢`
        }
      })),
      ...markers.filter(m => m.type === 'exit').map(m => ({
        x: new Date(m.timestamp * 1000).getTime(),
        y: m.price,
        marker: {
          size: 8,
          fillColor: '#f97316',
          strokeColor: '#c2410c',
          strokeWidth: 2,
        },
        label: {
          borderColor: '#f97316',
          style: {
            color: '#fff',
            background: '#f97316',
          },
          text: `Exit ${m.price}¢`
        }
      }))
    ]
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
        }
      },
      animations: {
        enabled: false
      }
    },
    theme: {
      mode: 'dark'
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#10b981',
          downward: '#ef4444'
        },
        wick: {
          useFillColor: true
        }
      }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        style: {
          colors: '#94a3b8',
          fontSize: '12px',
          fontWeight: 600
        },
        datetimeFormatter: {
          hour: 'h:mm TT'
        }
      }
    },
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        style: {
          colors: '#94a3b8',
          fontSize: '12px',
          fontWeight: 600
        },
        formatter: (value) => `${value}¢`
      }
    },
    grid: {
      borderColor: '#334155',
      strokeDashArray: 3,
      xaxis: {
        lines: {
          show: false
        }
      },
      yaxis: {
        lines: {
          show: true
        }
      }
    },
    tooltip: {
      theme: 'dark',
      custom: function({ dataPointIndex }: any) {
        const candle = candles[dataPointIndex]
        if (!candle) return ''

        return `
          <div class="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg p-4 shadow-2xl">
            <div class="text-gray-400 text-xs font-semibold mb-2">
              ${format(new Date(candle.timestamp * 1000), 'MMM d, h:mm a')}
            </div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1">
              <div class="text-gray-500 text-xs">Open:</div>
              <div class="text-white text-xs font-bold">${candle.open}¢</div>
              <div class="text-gray-500 text-xs">High:</div>
              <div class="text-green-400 text-xs font-bold">${candle.high}¢</div>
              <div class="text-gray-500 text-xs">Low:</div>
              <div class="text-red-400 text-xs font-bold">${candle.low}¢</div>
              <div class="text-gray-500 text-xs">Close:</div>
              <div class="text-${candle.close >= candle.open ? 'green' : 'red'}-400 text-xs font-bold">${candle.close}¢</div>
            </div>
            ${candle.volume > 0 ? `
              <div class="mt-2 pt-2 border-t border-slate-700">
                <div class="text-gray-500 text-xs">Ticks: ${candle.volume}</div>
              </div>
            ` : ''}
          </div>
        `
      }
    },
    annotations
  }

  return (
    <div className="w-full">
      <div className="bg-slate-900/50 rounded-xl border border-slate-700/50 p-4">
        <ReactApexChart
          options={options}
          series={series}
          type="candlestick"
          height={600}
        />
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-6 bg-green-500 border border-green-600 rounded-sm"></div>
          <span className="text-gray-400 text-sm font-semibold">Bullish Candle</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-6 bg-red-500 border border-red-600 rounded-sm"></div>
          <span className="text-gray-400 text-sm font-semibold">Bearish Candle</span>
        </div>
        {markers.some(m => m.type === 'entry') && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">↑</span>
            </div>
            <span className="text-gray-400 text-sm font-semibold">Entry</span>
          </div>
        )}
        {markers.some(m => m.type === 'exit') && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs">↓</span>
            </div>
            <span className="text-gray-400 text-sm font-semibold">Exit</span>
          </div>
        )}
      </div>
    </div>
  )
}
