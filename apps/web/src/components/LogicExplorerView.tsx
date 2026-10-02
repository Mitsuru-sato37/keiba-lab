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
        Back to Race
      </button>
      <p className="eyebrow">{race.raceId} / stored evidence</p>
      <h1 id="logic-explorer-heading">Logic Explorer</h1>
      <p>Every explanation below comes from the selected Golden Race evidence.</p>

      <StageTimeline
        stages={race.stages}
        selectedStageId={stage.stageId}
        onSelect={onSelectStage}
      />

      <article className="stage-evidence-card">
        <p className="eyebrow">Stage {race.stages.indexOf(stage) + 1}</p>
        <h2>{stage.label}</h2>

        <section aria-labelledby="inputs-heading">
          <h3 id="inputs-heading">Inputs</h3>
          <dl>
            {stage.inputs.map((item) => (
              <EvidenceRow key={item.label} label={item.label} value={item.value} />
            ))}
          </dl>
        </section>

        <section aria-labelledby="conditions-heading">
          <h3 id="conditions-heading">Conditions</h3>
          <ul>
            {stage.conditions.map((condition) => (
              <li key={condition}>{condition}</li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="outputs-heading">
          <h3 id="outputs-heading">Outputs</h3>
          <dl>
            {stage.outputs.map((item) => (
              <EvidenceRow key={item.label} label={item.label} value={item.value} />
            ))}
          </dl>
        </section>

        <section aria-labelledby="lineage-heading">
          <h3 id="lineage-heading">Lineage and versions</h3>
          <dl>
            <EvidenceRow label="Data snapshot" value={stage.lineage.dataSnapshot} />
            <EvidenceRow label="Feature version" value={stage.lineage.featureVersion} />
            <EvidenceRow label="Model version" value={stage.lineage.modelVersion} />
            <EvidenceRow label="Logic version" value={stage.lineage.logicVersion} />
            <EvidenceRow label="Seed" value={stage.lineage.seed} />
            <EvidenceRow label="Code version" value={stage.lineage.codeVersion} />
          </dl>
        </section>

        <section aria-labelledby="validation-heading">
          <h3 id="validation-heading">Validation evidence</h3>
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
