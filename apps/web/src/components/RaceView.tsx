import type { GoldenRaceCase } from "../goldenRaceFixture";
import { EvidenceRow } from "./EvidenceRow";
import { StageTimeline } from "./StageTimeline";
import { StatusBadge } from "./StatusBadge";
import { decisionLabel, strategyLabel } from "../uiLabels";

type RaceViewProps = {
  race: GoldenRaceCase;
  onBack: () => void;
  onExploreStage: (stageId: GoldenRaceCase["stages"][number]["stageId"]) => void;
};

export function RaceView({ race, onBack, onExploreStage }: RaceViewProps) {
  return (
    <section aria-labelledby="race-heading" className="view race-view">
      <button onClick={onBack} type="button">
        レース一覧に戻る
      </button>
      <div className="race-heading-row">
        <div>
          <p className="eyebrow">{race.raceId}</p>
          <h1 id="race-heading">レース詳細</h1>
          <p>{race.title}</p>
        </div>
        <StatusBadge decision={race.decision} />
      </div>

      <div className="summary-grid">
        <dl className="evidence-card">
          <EvidenceRow label="予想信頼度" value={`${Math.round(race.confidence * 100)}%`} />
          <EvidenceRow label="データ状態" value={race.dataStatus} />
          <EvidenceRow label="計算時刻" value={race.calculatedAt} />
          <EvidenceRow
            label="判定理由"
            value={race.reasonCodes.length > 0 ? `市場価値なし（${race.reasonCodes.join(", ")}）` : "市場価値あり"}
          />
        </dl>
        <div className="evidence-card gate-card">
          <h2>結果の表示条件</h2>
          <p>判定が保存されるまで、結果と払戻は表示されません。</p>
        </div>
      </div>

      <section aria-labelledby="strategy-heading">
        <h2 id="strategy-heading">買い方の候補</h2>
        <div className="strategy-grid">
          {race.strategies.map((strategy) => (
            <article className="strategy-card" key={strategy.name}>
              <h3>{strategyLabel(strategy.name)}</h3>
              <StatusBadge decision={strategy.decision} />
              <EvidenceRow label="候補数" value={strategy.candidateCount} />
              <EvidenceRow label="投資額" value={`${strategy.stake}円`} />
              <p>{strategy.explanation}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="stages-heading">
        <h2 id="stages-heading">計算の根拠</h2>
        <p>各ステップを選ぶと、使った入力と計算結果を確認できます。</p>
        <StageTimeline
          stages={race.stages}
          selectedStageId={race.stages[0].stageId}
          onSelect={onExploreStage}
        />
      </section>
    </section>
  );
}
