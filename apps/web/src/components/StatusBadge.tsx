import type { RecommendationDecision } from "../goldenRaceFixture";

type StatusBadgeProps = {
  decision: RecommendationDecision;
};

export function StatusBadge({ decision }: StatusBadgeProps) {
  return (
    <span className={`status-badge status-badge-${decision.toLowerCase()}`}>
      {decision}
    </span>
  );
}
