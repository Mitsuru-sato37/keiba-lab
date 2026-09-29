import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('shows the required product areas', () => {
    render(<App />)
    for (const label of ['Today', 'Race', 'Logic Explorer', 'Backtest', 'Performance', 'Settings']) {
      expect(screen.getByRole('navigation')).toHaveTextContent(label)
    }
  })
})
