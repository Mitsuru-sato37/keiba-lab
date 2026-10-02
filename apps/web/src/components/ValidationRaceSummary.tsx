import { firstValidationRace } from "../validationRaceFixture";
import { StatusBadge } from "./StatusBadge";

const percentage = (value: number): string => `${(value * 100).toFixed(1)}%`;

export function ValidationRaceSummary() {
  const race = firstValidationRace;

  return (
    <section aria-labelledby="validation-race-heading" className="validation-race-summary">
      <div className="validation-race-header">
        <div>
          <p className="eyebrow">2022 one-day validation</p>
          <h2 id="validation-race-heading">First validation race</h2>
          <p>{race.raceId}</p>
        </div>
        <StatusBadge decision={race.decision} />
      </div>

      <p className="fixture-note">Synthetic fixture: not actual JRA data.</p>

      <div className="summary-grid">
        <dl className="evidence-card">
          <div className="evidence-row">
            <dt>Date</dt>
            <dd>{race.targetDate}</dd>
          </div>
          <div className="evidence-row">
            <dt>As-of time</dt>
            <dd>{race.asOfTime}</dd>
          </div>
          <div className="evidence-row">
            <dt>Training data</dt>
            <dd>{race.trainingWindow}</dd>
          </div>
          <div className="evidence-row">
            <dt>Recommendation</dt>
            <dd>{race.decision}</dd>
          </div>
        </dl>

        <div className="evidence-card gate-card">
          <h3>Result</h3>
          {race.recommendationPersisted ? (
            <>
              <p>Recommendation persisted; result is available.</p>
              <p>Winner: {race.winnerId}</p>
              <p>{race.winPayoutYen} JPY</p>
            </>
          ) : (
            <p>Result and payout are unavailable until recommendation persistence.</p>
          )}
        </div>
      </div>

      <div className="validation-runner-table-wrap">
        <table className="validation-runner-table">
          <caption>Runner predictions</caption>
          <thead>
            <tr>
              <th scope="col">Runner</th>
              <th scope="col">Gate</th>
              <th scope="col">Win probability</th>
              <th scope="col">Finish</th>
            </tr>
          </thead>
          <tbody>
            {race.runners.map((runner) => (
              <tr key={runner.runnerId}>
                <th scope="row">{runner.runnerId}</th>
                <td>{runner.gate}</td>
                <td>{percentage(runner.winProbability)}</td>
                <td>{runner.finishPosition}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
