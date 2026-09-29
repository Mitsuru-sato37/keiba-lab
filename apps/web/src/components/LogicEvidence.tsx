import type { PredictionEvidence } from '../types'

export function LogicEvidence({ prediction }: { prediction: PredictionEvidence }) {
  return <section aria-label="Prediction evidence"><h2>Prediction evidence</h2><dl>
    <dt>Horse</dt><dd>{prediction.horse_id}</dd>
    <dt>Win probability</dt><dd>{prediction.win_probability}</dd>
    <dt>Uncertainty</dt><dd>{prediction.uncertainty}</dd>
    <dt>Snapshot</dt><dd>{prediction.prediction_snapshot_id}</dd>
    <dt>Logic</dt><dd>{prediction.logic_version}</dd>
  </dl></section>
}
