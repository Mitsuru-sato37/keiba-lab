import type { GoldenRaceCase } from "../goldenRaceFixture";
import { EvidenceRow } from "./EvidenceRow";
import { StageTimeline } from "./StageTimeline";
import { StatusBadge } from "./StatusBadge";

type RaceViewProps = {
  race: GoldenRaceCase;
  onBack: () => void;
  onExploreStage: (stageId: GoldenRaceCase["stages"][number]["stageId"]) => void;
};

export function RaceView({ race, onBack, onExploreStage }: RaceViewProps) {
  return (
    <section aria-labelledby="race-heading" className="view race-view">
      <button onClick={onBack} type="button">
        Back to Today
      </button>
      <div className="race-heading-row">
        <div>
          <p className="eyebrow">{race.raceId}</p>
          <h1 id="race-heading">Race</h1>
          <p>{race.title}</p>
        </div>
        <StatusBadge decision={race.decision} />
      </div>

      <div className="summary-grid">
        <dl className="evidence-card">
          <EvidenceRow label="Confidence" value={`${Math.round(race.confidence * 100)}%`} />
          <EvidenceRow label="Data status" value={race.dataStatus} />
          <EvidenceRow label="Calculated at" value={race.calculatedAt} />
          <EvidenceRow
            label="Reason"
            value={race.reasonCodes.length > 0 ? race.reasonCodes.join(", ") : "Positive market value"}
          />
        </dl>
        <div className="evidence-card gate-card">
          <h2>Result access</h2>
          <p>Result and payout: unavailable until recommendation persistence.</p>
        </div>
      </div>

      <section aria-labelledby="strategy-heading">
        <h2 id="strategy-heading">Strategies</h2>
        <div className="strategy-grid">
          {race.strategies.map((strategy) => (
            <article className="strategy-card" key={strategy.name}>
              <h3>{strategy.name}</h3>
              <StatusBadge decision={strategy.decision} />
              <EvidenceRow label="Candidates" value={strategy.candidateCount} />
              <EvidenceRow label="Stake" value={`${strategy.stake} JPY`} />
              <p>{strategy.explanation}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="stages-heading">
        <h2 id="stages-heading">Calculation evidence</h2>
        <p>Select a stage to inspect its stored inputs and outputs.</p>
        <StageTimeline
          stages={race.stages}
          selectedStageId={race.stages[0].stageId}
          onSelect={onExploreStage}
        />
      </section>
    </section>
  );
}
