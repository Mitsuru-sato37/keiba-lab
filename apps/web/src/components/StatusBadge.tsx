import type { RecommendationDecision } from "../goldenRaceFixture";
import { decisionLabel } from "../uiLabels";

type StatusBadgeProps = {
  decision: RecommendationDecision;
};

export function StatusBadge({ decision }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge-${decision.toLowerCase()}`}>
      {decisionLabel(decision)}
    </span>
  );
}
