import { useEffect, useState } from 'react'
import './App.css'
import { fetchRace, fetchToday } from './api'
import { RacePage } from './components/RacePage'
import { TodayPage } from './components/TodayPage'
import type { RaceDetail, RaceSummary, Recommendation } from './types'

const areas = ['Today', 'Race', 'Logic Explorer', 'Backtest', 'Performance', 'Settings']

function App() {
  const [races, setRaces] = useState<RaceSummary[]>([])
  const [detail, setDetail] = useState<RaceDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { fetchToday(new Date().toISOString().slice(0, 10)).then(setRaces).catch(() => setError('Unable to load races')) }, [])
  async function selectRace(raceId: string) { setError(null); try { setDetail(await fetchRace(raceId)) } catch { setError('Unable to load race') } }
  function updated(recommendation: Recommendation) { if (detail) setDetail({ ...detail, recommendation }) }
  return <main><h1>keiba-lab</h1><nav aria-label="Primary"><ul>{areas.map((area) => <li key={area}><button type="button" disabled={area !== 'Today' && area !== 'Race'}>{area}</button></li>)}</ul></nav>{error && <p role="alert">{error}</p>}{detail ? <RacePage detail={detail} onUpdated={updated} /> : <TodayPage races={races} onSelect={selectRace} />}</main>
}

export default App
