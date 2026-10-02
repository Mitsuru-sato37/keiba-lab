import type { GoldenStageId, StageEvidence } from "../goldenRaceFixture";

type StageTimelineProps = {
  stages: readonly StageEvidence[];
  selectedStageId: GoldenStageId;
  onSelect: (stageId: GoldenStageId) => void;
};

export function StageTimeline({
  stages,
  selectedStageId,
  onSelect,
}: StageTimelineProps) {
  return (
    <nav aria-label="計算ステップ" className="stage-timeline">
      {stages.map((stage) => (
        <button
          aria-current={stage.stageId === selectedStageId ? "step" : undefined}
          className={stage.stageId === selectedStageId ? "stage-selected" : ""}
          key={stage.stageId}
          onClick={() => onSelect(stage.stageId)}
          type="button"
        >
          {stage.label}
        </button>
      ))}
    </nav>
  );
}
