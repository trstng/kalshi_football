/**
 * Simple CSV parser utility
 */

export interface ScheduleGame {
  marketTicker: string
  marketTitle: string
  awayTeam: string
  homeTeam: string
  kickoffTs: number
  series: 'NFL' | 'CFB'
}

/**
 * Parse CSV text into an array of objects
 */
function parseCSV(text: string): Record<string, string>[] {
  const lines = text.trim().split('\n')
  if (lines.length === 0) return []

  // Trim headers to remove \r and whitespace
  const headers = lines[0].split(',').map(h => h.trim())
  const data: Record<string, string>[] = []

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim())
    const row: Record<string, string> = {}

    headers.forEach((header, index) => {
      row[header] = values[index] || ''
    })

    data.push(row)
  }

  return data
}

/**
 * Fetch and parse NFL schedule
 */
export async function fetchNFLSchedule(): Promise<ScheduleGame[]> {
  try {
    const response = await fetch('/schedules/nfl_schedule.csv')
    if (!response.ok) {
      console.error(`NFL schedule fetch failed: ${response.status} ${response.statusText}`)
      return []
    }

    const text = await response.text()
    const data = parseCSV(text)

    return data
      .map(row => ({
        marketTicker: row.market_ticker || '',
        marketTitle: row.market_title || '',
        awayTeam: row.away_team || '',
        homeTeam: row.home_team || '',
        kickoffTs: parseInt(row.strike_date || '0'),
        series: 'NFL' as const
      }))
      .filter(game => !isNaN(game.kickoffTs) && game.kickoffTs > 0)
  } catch (error) {
    console.error('Error fetching NFL schedule:', error)
    return []
  }
}

/**
 * Fetch and parse CFB schedule
 */
export async function fetchCFBSchedule(): Promise<ScheduleGame[]> {
  try {
    const response = await fetch('/schedules/cfb_schedule.csv')
    const text = await response.text()
    const data = parseCSV(text)

    return data
      .map(row => ({
        marketTicker: row.market_ticker || '',
        marketTitle: row.market_title || '',
        awayTeam: row.away_team || '',
        homeTeam: row.home_team || '',
        kickoffTs: parseInt(row.kickoff_ts || '0'),
        series: 'CFB' as const
      }))
      .filter(game => !isNaN(game.kickoffTs) && game.kickoffTs > 0)
  } catch (error) {
    console.error('Error fetching CFB schedule:', error)
    return []
  }
}

/**
 * Fetch and parse both schedules
 */
export async function fetchAllSchedules(): Promise<ScheduleGame[]> {
  const [nfl, cfb] = await Promise.all([
    fetchNFLSchedule(),
    fetchCFBSchedule()
  ])

  // Combine and sort by kickoff time
  return [...nfl, ...cfb].sort((a, b) => a.kickoffTs - b.kickoffTs)
}
