import { type Game } from '../lib/supabase'
import { format } from 'date-fns'
import MarketChart from './MarketChart'

type GameDetailModalProps = {
  game: Game
  onClose: () => void
}

export default function GameDetailModal({ game, onClose }: GameDetailModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="relative w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="relative group">
          {/* Glow effect */}
          <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 rounded-2xl blur-xl opacity-50"></div>

          {/* Modal Content */}
          <div className="relative bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900 rounded-2xl border border-slate-700/50 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-5 border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                  <h2 className="text-3xl font-black text-white">
                    {game.market_title}
                  </h2>
                </div>
                <p className="text-gray-400 text-lg">{game.yes_subtitle}</p>
                <div className="flex items-center gap-4 mt-3">
                  <div className="inline-flex items-center gap-2 bg-blue-500/10 px-3 py-1.5 rounded-full border border-blue-500/30">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-blue-300 font-semibold text-sm">
                      Kickoff: {format(new Date(game.kickoff_ts * 1000), 'MMM d, h:mm a')}
                    </span>
                  </div>
                  <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    game.status === 'triggered'
                      ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                      : 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                  }`}>
                    {game.status}
                  </span>
                  {game.is_eligible !== null && (
                    <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                      game.is_eligible
                        ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                        : 'bg-red-500/20 text-red-400 border border-red-500/50'
                    }`}>
                      {game.is_eligible ? '✓ Eligible' : '✗ Not Eligible'}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={onClose}
                className="ml-4 text-gray-400 hover:text-white transition-colors p-2 hover:bg-slate-700/50 rounded-lg"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Checkpoint Data */}
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Checkpoint Odds</h3>
              <div className="grid grid-cols-3 gap-4">
                {/* 6h Checkpoint */}
                <div className="bg-slate-800/50 rounded-lg p-4 border border-blue-500/20">
                  <div className="text-gray-500 text-xs font-semibold mb-2">6 Hours Before</div>
                  {game.odds_6h ? (
                    <>
                      <div className="text-3xl font-black text-blue-400 mb-1">
                        {(game.odds_6h * 100).toFixed(1)}%
                      </div>
                      {game.checkpoint_6h_ts && (
                        <div className="text-gray-500 text-xs">
                          {format(new Date(game.checkpoint_6h_ts * 1000), 'h:mm a')}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-gray-600 text-sm">Pending</div>
                  )}
                </div>

                {/* 3h Checkpoint */}
                <div className="bg-slate-800/50 rounded-lg p-4 border border-purple-500/20">
                  <div className="text-gray-500 text-xs font-semibold mb-2">3 Hours Before</div>
                  {game.odds_3h ? (
                    <>
                      <div className="text-3xl font-black text-purple-400 mb-1">
                        {(game.odds_3h * 100).toFixed(1)}%
                      </div>
                      {game.checkpoint_3h_ts && (
                        <div className="text-gray-500 text-xs">
                          {format(new Date(game.checkpoint_3h_ts * 1000), 'h:mm a')}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-gray-600 text-sm">Pending</div>
                  )}
                </div>

                {/* 30m Checkpoint */}
                <div className="bg-slate-800/50 rounded-lg p-4 border border-green-500/20">
                  <div className="text-gray-500 text-xs font-semibold mb-2">30 Minutes Before</div>
                  {game.odds_30m ? (
                    <>
                      <div className="text-3xl font-black text-green-400 mb-1">
                        {(game.odds_30m * 100).toFixed(1)}%
                      </div>
                      {game.checkpoint_30m_ts && (
                        <div className="text-gray-500 text-xs">
                          {format(new Date(game.checkpoint_30m_ts * 1000), 'h:mm a')}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-gray-600 text-sm">Pending</div>
                  )}
                </div>
              </div>
            </div>

            {/* Market Chart */}
            <div className="px-6 py-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1 h-6 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
                <h3 className="text-2xl font-bold text-white">Market Price History</h3>
              </div>
              <MarketChart game={game} />
            </div>

            {/* Footer with Market Info */}
            <div className="px-6 py-4 border-t border-slate-700/50 bg-slate-900/50">
              <div className="flex items-center justify-between text-sm">
                <div className="text-gray-500">
                  <span className="font-mono font-semibold">{game.market_ticker}</span>
                </div>
                <div className="text-gray-500">
                  Event: <span className="font-mono font-semibold">{game.event_ticker}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
