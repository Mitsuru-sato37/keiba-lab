import { firstValidationRace } from "../validationRaceFixture";
import { decisionLabel } from "../uiLabels";
import { StatusBadge } from "./StatusBadge";

const percentage = (value: number): string => `${(value * 100).toFixed(1)}%`;

const formatJapaneseDate = (value: string): string => {
  const date = new Date(`${value}T00:00:00+09:00`);
  const parts = new Intl.DateTimeFormat("ja-JP", {
    day: "numeric",
    month: "numeric",
    timeZone: "Asia/Tokyo",
    year: "numeric",
  })
    .formatToParts(date)
    .reduce<Record<string, string>>((result, part) => {
      result[part.type] = part.value;
      return result;
    }, {});

  return `${parts.year}年${parts.month}月${parts.day}日`;
};

const formatJapaneseDateTime = (value: string): string => {
  const parts = new Intl.DateTimeFormat("ja-JP", {
    day: "numeric",
    hour: "2-digit",
    hourCycle: "h23",
    minute: "2-digit",
    month: "numeric",
    timeZone: "Asia/Tokyo",
    year: "numeric",
  })
    .formatToParts(new Date(value))
    .reduce<Record<string, string>>((result, part) => {
      result[part.type] = part.value;
      return result;
    }, {});

  return `${parts.year}年${parts.month}月${parts.day}日 ${parts.hour}:${parts.minute}（日本時間）`;
};

export function ValidationRaceSummary() {
  const race = firstValidationRace;
  const winningRunnerNumber =
    race.runners.findIndex((runner) => runner.runnerId === race.winnerId) + 1;

  return (
    <section aria-labelledby="validation-overview-heading" className="validation-race-summary">
      <section aria-labelledby="validation-overview-heading" className="summary-overview">
        <h2 id="validation-overview-heading">まず見る情報</h2>
        <div className="validation-race-header">
          <div>
            <p className="eyebrow">検証用レース</p>
            <h3>{formatJapaneseDate(race.targetDate)} 1R</h3>
            <p className="summary-kicker">2022年最初の検証レース</p>
          </div>
          <StatusBadge decision={race.decision} />
        </div>

        <div className="summary-key-facts">
          <div className="summary-key-fact summary-key-fact-primary">
            <span>判定</span>
            <strong>{decisionLabel(race.decision)}</strong>
          </div>
          <div className="summary-key-fact">
            <span>勝ち馬</span>
            <strong>{winningRunnerNumber}番</strong>
          </div>
          <div className="summary-key-fact">
            <span>払戻</span>
            <strong>{race.winPayoutYen.toLocaleString("ja-JP")}円</strong>
          </div>
        </div>
      </section>

      <section aria-labelledby="validation-details-heading" className="summary-details">
        <div className="summary-section-heading">
          <p className="eyebrow">予想と結果の中身</p>
          <h2 id="validation-details-heading">詳しい内容</h2>
        </div>

        <dl className="summary-detail-list">
          <div className="evidence-row">
            <dt>対象日</dt>
            <dd>{formatJapaneseDate(race.targetDate)}</dd>
          </div>
          <div className="evidence-row">
            <dt>予想時点</dt>
            <dd>{formatJapaneseDateTime(race.asOfTime)}</dd>
          </div>
          <div className="evidence-row">
            <dt>学習期間</dt>
            <dd>{race.trainingWindow.replace("–", "〜")}年</dd>
          </div>
        </dl>

        <div className="validation-runner-table-wrap">
          <table aria-label="出走馬の予想" className="validation-runner-table">
            <caption>出走馬の予想</caption>
            <thead>
              <tr>
                <th scope="col">馬番</th>
                <th scope="col">枠番</th>
                <th scope="col">予想勝率</th>
                <th scope="col">結果</th>
              </tr>
            </thead>
            <tbody>
              {race.runners.map((runner, index) => (
                <tr key={runner.runnerId}>
                  <th scope="row">{index + 1}番</th>
                  <td>{runner.gate}</td>
                  <td>{percentage(runner.winProbability)}</td>
                  <td>{runner.finishPosition}着</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-labelledby="validation-notes-heading" className="summary-notes">
        <div className="summary-section-heading">
          <p className="eyebrow">確認しておきたいこと</p>
          <h2 id="validation-notes-heading">備考</h2>
        </div>
        <p className="fixture-note">
          検証用の合成テストデータです。実際のJRAデータや実際の予想結果ではありません。
        </p>
        <p className="trace-note">追跡用レースID：{race.raceId}</p>
        {race.recommendationPersisted ? (
          <p className="trace-note">判定が保存された後のため、結果と払戻を表示しています。</p>
        ) : (
          <p className="trace-note">判定が保存されるまで、結果と払戻は表示されません。</p>
        )}
      </section>
    </section>
  );
}
