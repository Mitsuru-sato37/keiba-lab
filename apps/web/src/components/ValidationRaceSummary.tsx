import { firstValidationRace } from "../validationRaceFixture";
import { decisionLabel } from "../uiLabels";
import { StatusBadge } from "./StatusBadge";

const percentage = (value: number): string => `${(value * 100).toFixed(1)}%`;

export function ValidationRaceSummary() {
  const race = firstValidationRace;

  return (
    <section aria-labelledby="validation-race-heading" className="validation-race-summary">
      <div className="validation-race-header">
        <div>
          <p className="eyebrow">2022年・1日分の検証</p>
          <h2 id="validation-race-heading">2022年最初の検証レース</h2>
          <p>{race.raceId}</p>
        </div>
        <StatusBadge decision={race.decision} />
      </div>

      <p className="fixture-note">合成テストデータです。実際のJRAデータではありません。</p>

      <div className="summary-grid">
        <dl className="evidence-card">
          <div className="evidence-row">
            <dt>対象日</dt>
            <dd>{race.targetDate}</dd>
          </div>
          <div className="evidence-row">
            <dt>予想時点</dt>
            <dd>{race.asOfTime}</dd>
          </div>
          <div className="evidence-row">
            <dt>学習期間</dt>
            <dd>{race.trainingWindow}</dd>
          </div>
          <div className="evidence-row">
            <dt>判定</dt>
            <dd>{decisionLabel(race.decision)}</dd>
          </div>
        </dl>

        <div className="evidence-card gate-card">
          <h3>結果</h3>
          {race.recommendationPersisted ? (
            <>
              <p>判定が保存済みのため、結果を表示しています。</p>
              <p>勝ち馬：{race.winnerId}</p>
              <p>{race.winPayoutYen}円</p>
            </>
          ) : (
            <p>判定が保存されるまで、結果と払戻は表示されません。</p>
          )}
        </div>
      </div>

      <div className="validation-runner-table-wrap">
        <table className="validation-runner-table">
          <caption>出走馬ごとの予想</caption>
          <thead>
            <tr>
              <th scope="col">出走馬</th>
              <th scope="col">枠</th>
              <th scope="col">勝率予測</th>
              <th scope="col">着順</th>
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
