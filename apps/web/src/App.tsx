import './App.css'

const areas = ['Today', 'Race', 'Logic Explorer', 'Backtest', 'Performance', 'Settings']

function App() {
  return (
    <main>
      <h1>keiba-lab</h1>
      <nav aria-label="Primary">
        <ul>
          {areas.map((area) => (
            <li key={area}>
              <button type="button">{area}</button>
            </li>
          ))}
        </ul>
      </nav>
    </main>
  )
}

export default App
