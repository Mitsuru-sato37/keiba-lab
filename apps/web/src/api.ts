import type { RaceDetail, RaceSummary, Recommendation } from './types'

export async function fetchToday(date: string): Promise<RaceSummary[]> {
  const response = await fetch(`/races?date=${date}&as_of=${new Date().toISOString()}`)
  if (!response.ok) throw new Error('Unable to load races')
  return response.json() as Promise<RaceSummary[]>
}

export async function fetchRace(raceId: string): Promise<RaceDetail> {
  const response = await fetch(`/races/${raceId}?as_of=${new Date().toISOString()}`)
  if (!response.ok) throw new Error('Unable to load race')
  return response.json() as Promise<RaceDetail>
}

export async function updateOdds(raceId: string, odds: string): Promise<Recommendation> {
  const response = await fetch(`/races/${raceId}/odds`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ odds, calculated_at: new Date().toISOString() }) })
  if (!response.ok) throw new Error('Unable to update odds')
  return response.json() as Promise<Recommendation>
}
