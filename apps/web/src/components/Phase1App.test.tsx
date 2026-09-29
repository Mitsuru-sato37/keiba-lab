import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'

describe('Phase 1 application flow', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url.includes('/races?')) {
        return Promise.resolve(new Response(JSON.stringify([{ race_id: 'R1', post_time: '2022-01-01T06:00:00Z', runner_count: 1, data_status: 'READY', recommendation_state: 'WAIT' }]), { status: 200 }))
      }
      return Promise.resolve(new Response(JSON.stringify({ race_id: 'R1', post_time: '2022-01-01T06:00:00Z', prediction: { horse_id: 'H1', win_probability: '0.25', uncertainty: '0.10', prediction_snapshot_id: 'P1', logic_version: 'MODEL-WIN-001:v1' }, recommendation: { decision: 'WAIT', reason_codes: ['ODDS_UNAVAILABLE'], policy_version: 'POLICY-WIN-001:v1' } }), { status: 200 }))
    }))
  })

  it('navigates Today to Race and shows evidence', async () => {
    render(<App />)
    expect(screen.getByRole('navigation')).toHaveTextContent('Today')
    await waitFor(() => expect(screen.getByRole('button', { name: /R1/ })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /R1/ }))
    await waitFor(() => expect(screen.getByText('WAIT')).toBeInTheDocument())
    expect(screen.getByText('Prediction evidence')).toBeInTheDocument()
    expect(screen.getByText('Fair odds unavailable')).toBeInTheDocument()
  })
})
