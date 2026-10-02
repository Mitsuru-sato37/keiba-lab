import type { GoldenRaceCase } from "../goldenRaceFixture";
import { StatusBadge } from "./StatusBadge";

type TodayViewProps = {
  cases: readonly GoldenRaceCase[];
  onSelectRace: (caseId: GoldenRaceCase["caseId"]) => void;
};

export function TodayView({ cases, onSelectRace }: TodayViewProps) {
  return (
    <section aria-labelledby="today-heading" className="view today-view">
      <p className="eyebrow">keiba-lab / Today</p>
      <h1 id="today-heading">Today</h1>
      <p>Deterministic Golden Race fixture cases for UI tracing.</p>
      <div className="race-card-grid">
        {cases.map((race) => (
          <article className="race-card" key={race.caseId}>
            <div className="race-card-header">
              <div>
                <p className="eyebrow">{race.raceId}</p>
                <h2>{race.title}</h2>
              </div>
              <StatusBadge decision={race.decision} />
            </div>
            <p>
              {race.surface} / {race.distanceM}m / {race.fieldSize} runners
            </p>
            <p>Confidence: {Math.round(race.confidence * 100)}%</p>
            <button
              onClick={() => onSelectRace(race.caseId)}
              type="button"
            >
              Open {race.title}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
