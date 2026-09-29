import type { RaceSummary } from '../types'

export function TodayPage({ races, onSelect }: { races: RaceSummary[]; onSelect: (raceId: string) => void }) {
  return <section><h2>Today</h2><ul>{races.map((race) => <li key={race.race_id}><button type="button" onClick={() => onSelect(race.race_id)}>{race.race_id} · {race.recommendation_state}</button><span> {race.data_status}</span></li>)}</ul></section>
}
