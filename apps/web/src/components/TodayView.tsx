import type { GoldenRaceCase } from "../goldenRaceFixture";
import { StatusBadge } from "./StatusBadge";
import { ValidationRaceSummary } from "./ValidationRaceSummary";

type TodayViewProps = {
  cases: readonly GoldenRaceCase[];
  onSelectRace: (caseId: GoldenRaceCase["caseId"]) => void;
};

export function TodayView({ cases, onSelectRace }: TodayViewProps) {
  return (
    <section aria-labelledby="today-heading" className="view today-view">
      <p className="eyebrow">keiba-lab / レース一覧</p>
      <h1 id="today-heading">レース一覧</h1>
      <p>検証用のレース予想と、その判断の根拠を確認できます。</p>
      <ValidationRaceSummary />
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
              {race.surface === "turf" ? "芝" : "ダート"} / {race.distanceM}m / {race.fieldSize}頭
            </p>
            <p>予想信頼度: {Math.round(race.confidence * 100)}%</p>
            <button
              onClick={() => onSelectRace(race.caseId)}
              type="button"
            >
              詳細を見る：{race.title}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
