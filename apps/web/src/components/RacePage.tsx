import { useState } from 'react'
import { updateOdds } from '../api'
import type { RaceDetail } from '../types'
import { LogicEvidence } from './LogicEvidence'

export function RacePage({ detail, onUpdated }: { detail: RaceDetail; onUpdated: (recommendation: RaceDetail['recommendation']) => void }) {
  const [odds, setOdds] = useState('')
  const recommendation = detail.recommendation
  async function submitOdds() {
    if (!odds) return
    onUpdated(await updateOdds(detail.race_id, odds))
    setOdds('')
  }
  return <section><button type="button" onClick={() => onUpdated(recommendation)}>← Today</button><h2>Race {detail.race_id}</h2><p aria-label="Decision">{recommendation.decision}</p><LogicEvidence prediction={detail.prediction} /><dl>
    <dt>Fair odds</dt><dd>{recommendation.fair_odds ?? 'Fair odds unavailable'}</dd>
    <dt>Current odds</dt><dd>{recommendation.odds ?? 'Not entered'}</dd>
    <dt>Expected value</dt><dd>{recommendation.expected_value ?? 'Not evaluated'}</dd>
    <dt>Reason</dt><dd>{recommendation.reason_codes.join(', ')}</dd>
    <dt>Policy</dt><dd>{recommendation.policy_version}</dd>
  </dl><label>Manual win odds <input aria-label="Manual win odds" value={odds} onChange={(event) => setOdds(event.target.value)} inputMode="decimal" /></label><button type="button" onClick={submitOdds}>Evaluate odds</button></section>
}
