import { useEffect, useState } from 'react'
import { format, isToday } from 'date-fns'
import { fetchNFLSchedule, fetchCFBSchedule, type ScheduleGame } from '../lib/csv'

type FilterType = 'all' | 'today' | 'this-week'
type SeriesType = 'NFL' | 'CFB'

export default function Schedule() {
  const [nflGames, setNflGames] = useState<ScheduleGame[]>([])
  const [cfbGames, setCfbGames] = useState<ScheduleGame[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<SeriesType>('NFL')
  const [filter, setFilter] = useState<FilterType>('all')

  useEffect(() => {
    loadSchedules()
  }, [])

  async function loadSchedules() {
    setLoading(true)
    const [nfl, cfb] = await Promise.all([
      fetchNFLSchedule(),
      fetchCFBSchedule()
    ])
    setNflGames(nfl)
    setCfbGames(cfb)
    setLoading(false)
  }

  function filterGames(games: ScheduleGame[]): ScheduleGame[] {
    const now = Date.now() / 1000
    const sevenDaysFromNow = now + (7 * 24 * 60 * 60)

    // Only show future games
    let filtered = games.filter(game => game.kickoffTs > now)

    if (filter === 'today') {
      filtered = filtered.filter(game => isToday(new Date(game.kickoffTs * 1000)))
    } else if (filter === 'this-week') {
      // Show games in the next 7 days
      filtered = filtered.filter(game => game.kickoffTs <= sevenDaysFromNow)
    }

    // Sort by kickoff time (earliest first)
    return filtered.sort((a, b) => a.kickoffTs - b.kickoffTs)
  }

  const displayGames = filterGames(activeTab === 'NFL' ? nflGames : cfbGames)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-black mb-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Game Schedule
          </h1>
          <p className="text-gray-400 text-lg">All tracked games from Kalshi markets</p>
        </div>

        {/* Controls */}
        <div className="mb-6 flex flex-wrap gap-4 items-center justify-between">
          {/* Series Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('NFL')}
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                activeTab === 'NFL'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              NFL
            </button>
            <button
              onClick={() => setActiveTab('CFB')}
              className={`px-6 py-2.5 rounded-xl font-bold text-sm transition-all duration-200 ${
                activeTab === 'CFB'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/50'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              CFB
            </button>
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all ${
                filter === 'all'
                  ? 'bg-slate-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              All Games
            </button>
            <button
              onClick={() => setFilter('this-week')}
              className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all ${
                filter === 'this-week'
                  ? 'bg-slate-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Next 7 Days
            </button>
            <button
              onClick={() => setFilter('today')}
              className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all ${
                filter === 'today'
                  ? 'bg-slate-700 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              Today
            </button>
          </div>
        </div>

        {/* Games Table */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/50 to-purple-600/50 rounded-2xl blur opacity-20"></div>
          <div className="relative bg-slate-800/90 backdrop-blur-xl rounded-2xl border border-slate-700/50 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-900/50">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
                  Upcoming {activeTab} Games
                </h2>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-gray-400 text-sm font-semibold">{displayGames.length} games</span>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="px-6 py-16 text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                <p className="text-gray-400 mt-4">Loading schedule...</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700/50">
                      <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                        Matchup
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                        Date & Time
                      </th>
                      <th className="px-6 py-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider">
                        Market Ticker
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayGames.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-6 py-12 text-center">
                          <div className="flex flex-col items-center gap-3">
                            <svg className="w-16 h-16 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <p className="text-gray-400 text-lg">No games found</p>
                            <p className="text-gray-500 text-sm">
                              {filter === 'today' && 'No games scheduled for today'}
                              {filter === 'this-week' && 'No games in the next 7 days'}
                              {filter === 'all' && 'No upcoming games in schedule'}
                            </p>
                          </div>
                        </td>
                      </tr>
                    ) : (
                      displayGames.map((game, index) => {
                        const kickoffDate = new Date(game.kickoffTs * 1000)
                        const isTodayGame = isToday(kickoffDate)

                        return (
                          <tr
                            key={index}
                            className={`border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors ${
                              isTodayGame ? 'bg-purple-500/10' : ''
                            }`}
                          >
                            <td className="px-6 py-4">
                              <div className="flex items-center gap-3">
                                {isTodayGame && (
                                  <div className="flex items-center gap-1.5 bg-green-500/20 px-2 py-1 rounded border border-green-500/50">
                                    <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                                    <span className="text-green-400 font-bold text-xs uppercase">Today</span>
                                  </div>
                                )}
                                <div>
                                  <div className="font-bold text-white text-lg">
                                    {game.awayTeam} @ {game.homeTeam}
                                  </div>
                                  <div className="text-gray-500 text-sm">{game.marketTitle}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="text-white font-semibold">
                                {format(kickoffDate, 'EEE, MMM d')}
                              </div>
                              <div className="text-gray-400 text-sm">
                                {format(kickoffDate, 'h:mm a zzz')}
                              </div>
                            </td>
                            <td className="px-6 py-4">
                              <div className="inline-flex items-center gap-2 bg-slate-700/50 px-3 py-1.5 rounded-lg border border-slate-600/50">
                                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                </svg>
                                <span className="text-gray-300 font-mono text-sm">{game.marketTicker}</span>
                              </div>
                            </td>
                          </tr>
                        )
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Stats Footer */}
        <div className="mt-6 flex items-center justify-between text-sm text-gray-500">
          <div>
            Total tracked: {nflGames.length} NFL games, {cfbGames.length} CFB games
          </div>
          <div>
            Showing {displayGames.length} {filter === 'all' ? 'upcoming' : filter === 'today' ? 'today' : 'in next 7 days'}
          </div>
        </div>
      </div>
    </div>
  )
}
