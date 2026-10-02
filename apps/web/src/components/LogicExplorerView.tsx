import {
  getStageEvidence,
  type GoldenRaceCase,
  type GoldenStageId,
} from "../goldenRaceFixture";
import { EvidenceRow } from "./EvidenceRow";
import { StageTimeline } from "./StageTimeline";

type LogicExplorerViewProps = {
  race: GoldenRaceCase;
  stageId: GoldenStageId;
  onBack: () => void;
  onSelectStage: (stageId: GoldenStageId) => void;
};

export function LogicExplorerView({
  race,
  stageId,
  onBack,
  onSelectStage,
}: LogicExplorerViewProps) {
  const stage = getStageEvidence(race, stageId);

  return (
    <section
      aria-labelledby="logic-explorer-heading"
      className="view logic-explorer-view"
    >
      <button onClick={onBack} type="button">
        レース詳細に戻る
      </button>
      <p className="eyebrow">{race.raceId} / 保存済みの根拠</p>
      <h1 id="logic-explorer-heading">予想の根拠</h1>
      <p>以下の説明は、選択した検証レースに保存された情報から表示しています。</p>

      <StageTimeline
        stages={race.stages}
        selectedStageId={stage.stageId}
        onSelect={onSelectStage}
      />

      <article className="stage-evidence-card">
        <p className="eyebrow">計算ステップ {race.stages.indexOf(stage) + 1}</p>
        <h2>{stage.label}</h2>

        <section aria-labelledby="inputs-heading">
          <h3 id="inputs-heading">入力</h3>
          <dl>
            {stage.inputs.map((item) => (
              <EvidenceRow key={item.label} label={item.label} value={item.value} />
            ))}
          </dl>
        </section>

        <section aria-labelledby="conditions-heading">
          <h3 id="conditions-heading">条件</h3>
          <ul>
            {stage.conditions.map((condition) => (
              <li key={condition}>{condition}</li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="outputs-heading">
          <h3 id="outputs-heading">出力</h3>
          <dl>
            {stage.outputs.map((item) => (
              <EvidenceRow key={item.label} label={item.label} value={item.value} />
            ))}
          </dl>
        </section>

        <section aria-labelledby="lineage-heading">
          <h3 id="lineage-heading">データの系譜とバージョン</h3>
          <dl>
            <EvidenceRow label="データスナップショット" value={stage.lineage.dataSnapshot} />
            <EvidenceRow label="特徴量バージョン" value={stage.lineage.featureVersion} />
            <EvidenceRow label="モデルバージョン" value={stage.lineage.modelVersion} />
            <EvidenceRow label="ロジックバージョン" value={stage.lineage.logicVersion} />
            <EvidenceRow label="乱数種" value={stage.lineage.seed} />
            <EvidenceRow label="コードバージョン" value={stage.lineage.codeVersion} />
          </dl>
        </section>

        <section aria-labelledby="validation-heading">
          <h3 id="validation-heading">検証情報</h3>
          <ul>
            {stage.validationReferences.map((reference) => (
              <li key={reference}>{reference}</li>
            ))}
          </ul>
        </section>
      </article>
    </section>
  );
}
