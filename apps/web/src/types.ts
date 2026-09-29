export type RaceSummary = {
  race_id: string
  post_time: string
  runner_count: number
  data_status: string
  recommendation_state: 'BUY' | 'SKIP' | 'WAIT'
}

export type PredictionEvidence = {
  race_id: string
  horse_id: string
  win_probability: string
  uncertainty: string
  prediction_snapshot_id: string
  logic_version: string
  calculated_at: string
}

export type Recommendation = {
  decision: 'BUY' | 'SKIP' | 'WAIT'
  reason_codes: string[]
  fair_odds?: string
  expected_value?: string
  policy_version: string
  prediction_snapshot_id: string
  odds?: string
}

export type RaceDetail = {
  race_id: string
  post_time: string
  prediction: PredictionEvidence
  recommendation: Recommendation
}
