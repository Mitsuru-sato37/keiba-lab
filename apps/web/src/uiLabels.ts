import type {
  RecommendationDecision,
  StrategySummary,
} from "./goldenRaceFixture";

export const decisionLabel = (decision: RecommendationDecision): string =>
  decision === "BUY" ? "購入" : "見送り";

export const strategyLabel = (name: StrategySummary["name"]): string => {
  const labels: Record<StrategySummary["name"], string> = {
    Stable: "安定型",
    Balanced: "バランス型",
    Longshot: "穴狙い",
  };
  return labels[name];
};

export const surfaceLabel = (surface: "turf" | "dirt"): string =>
  surface === "turf" ? "芝" : "ダート";
