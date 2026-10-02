export const GOLDEN_STAGE_ORDER = [
  "data_snapshot",
  "feature_snapshot",
  "ability_prediction",
  "calibration",
  "simulation",
  "bet_probability",
  "odds_snapshot",
  "expected_value",
  "strategy",
  "money_allocation",
  "recommendation",
] as const;

export type GoldenStageId = (typeof GOLDEN_STAGE_ORDER)[number];
export type RecommendationDecision = "BUY" | "SKIP";

export type EvidenceValue = string | number | boolean | null;

export type EvidenceItem = {
  label: string;
  value: EvidenceValue;
};

export type LineageSummary = {
  dataSnapshot: string;
  featureVersion: string;
  modelVersion: string;
  logicVersion: string;
  seed: number | null;
  codeVersion: string | null;
};

export type StageEvidence = {
  stageId: GoldenStageId;
  label: string;
  inputs: EvidenceItem[];
  conditions: string[];
  outputs: EvidenceItem[];
  lineage: LineageSummary;
  validationReferences: string[];
};

export type StrategySummary = {
  name: "Stable" | "Balanced" | "Longshot";
  decision: RecommendationDecision;
  candidateCount: number;
  stake: number;
  explanation: string;
};

export type GoldenRaceCase = {
  caseId: "golden-buy" | "golden-skip";
  raceId: string;
  title: string;
  surface: "turf" | "dirt";
  distanceM: number;
  fieldSize: number;
  asOfTime: string;
  oddsSnapshotTime: string;
  decision: RecommendationDecision;
  reasonCodes: string[];
  confidence: number;
  dataStatus: string;
  calculatedAt: string;
  strategies: StrategySummary[];
  stages: StageEvidence[];
};

const sharedLineage = (caseId: string, stageId: GoldenStageId): LineageSummary => ({
  dataSnapshot: `snapshot-${caseId}`,
  featureVersion: "FEATURE-CORE-V1",
  modelVersion: "MODEL-BASE-001",
  logicVersion:
    stageId === "recommendation"
      ? "LOGIC-REC-001"
      : `LOGIC-${stageId.toUpperCase()}`,
  seed: 20220101,
  codeVersion: "phase-6-golden-race",
});

const stageLabels: Record<GoldenStageId, string> = {
  data_snapshot: "Data snapshot",
  feature_snapshot: "Feature snapshot",
  ability_prediction: "Ability prediction",
  calibration: "Calibration",
  simulation: "Virtual race simulation",
  bet_probability: "Bet probability",
  odds_snapshot: "Odds snapshot",
  expected_value: "Expected value",
  strategy: "Strategy decision",
  money_allocation: "Money allocation",
  recommendation: "Recommendation",
};

const marketStages = new Set<GoldenStageId>([
  "odds_snapshot",
  "expected_value",
  "strategy",
  "money_allocation",
  "recommendation",
]);

const createStages = (
  caseId: string,
  surface: "turf" | "dirt",
  decision: RecommendationDecision,
): StageEvidence[] =>
  GOLDEN_STAGE_ORDER.map((stageId) => {
    const isMarketStage = marketStages.has(stageId);
    const stage: StageEvidence = {
      stageId,
      label: stageLabels[stageId],
      inputs: [
        { label: "Race snapshot", value: `snapshot-${caseId}` },
        { label: "Surface", value: surface },
      ],
      conditions: [
        "Only data received by the calculation as-of time is eligible",
        isMarketStage
          ? "Market evidence is evaluated after prediction persistence"
          : "Current-race odds are excluded from ability evidence",
      ],
      outputs: [
        { label: "Stage status", value: "succeeded" },
        { label: "Result", value: null },
        { label: "Payout", value: null },
      ],
      lineage: sharedLineage(caseId, stageId),
      validationReferences: ["LEAK-001", "VERSION-001"],
    };

    if (stageId === "ability_prediction") {
      stage.inputs.push({ label: "Form score features", value: "3 runners" });
      stage.outputs.push({ label: "Top runner", value: "horse-1 / horse-4" });
    }

    if (stageId === "odds_snapshot") {
      stage.inputs.push({ label: "Current-race odds", value: "2.8 / 4.0 / 8.0" });
      stage.outputs.push({ label: "Odds received", value: "2022-01-01 09:30 UTC" });
    }

    if (stageId === "recommendation") {
      stage.outputs.push({ label: "Decision", value: decision });
      stage.outputs.push({
        label: "Reason",
        value: decision === "BUY" ? "Positive market value" : "SKIP_NO_VALUE",
      });
    }

    return stage;
  });

const makeCase = (
  caseId: GoldenRaceCase["caseId"],
  raceId: string,
  title: string,
  surface: "turf" | "dirt",
  distanceM: number,
  decision: RecommendationDecision,
): GoldenRaceCase => ({
  caseId,
  raceId,
  title,
  surface,
  distanceM,
  fieldSize: 3,
  asOfTime: "2022-01-01T09:00:00Z",
  oddsSnapshotTime: "2022-01-01T09:35:00Z",
  decision,
  reasonCodes: decision === "SKIP" ? ["SKIP_NO_VALUE"] : [],
  confidence: decision === "BUY" ? 0.82 : 0.79,
  dataStatus: "Complete through recommendation; result and payout gated",
  calculatedAt: "2022-01-01T09:35:00Z",
  strategies: [
    {
      name: "Stable",
      decision,
      candidateCount: decision === "BUY" ? 1 : 0,
      stake: decision === "BUY" ? 200 : 0,
      explanation:
        decision === "BUY" ? "Positive value within the stable cap" : "No acceptable market value",
    },
    {
      name: "Balanced",
      decision,
      candidateCount: decision === "BUY" ? 1 : 0,
      stake: decision === "BUY" ? 300 : 0,
      explanation:
        decision === "BUY" ? "Value and confidence clear the balanced threshold" : "Value threshold not met",
    },
    {
      name: "Longshot",
      decision: "SKIP",
      candidateCount: 0,
      stake: 0,
      explanation: "No longshot candidate is eligible in this fixture",
    },
  ],
  stages: createStages(caseId, surface, decision),
});

export const goldenRaceCases: readonly GoldenRaceCase[] = [
  makeCase("golden-buy", "golden-race-buy", "Golden Race BUY", "turf", 1600, "BUY"),
  makeCase("golden-skip", "golden-race-skip", "Golden Race SKIP", "dirt", 1400, "SKIP"),
];

export const getGoldenRaceCase = (caseId: GoldenRaceCase["caseId"]): GoldenRaceCase => {
  const race = goldenRaceCases.find((candidate) => candidate.caseId === caseId);
  if (!race) {
    throw new Error(`Unknown Golden Race case: ${caseId}`);
  }
  return race;
};

export const getStageEvidence = (
  race: GoldenRaceCase,
  stageId: GoldenStageId,
): StageEvidence => {
  const stage = race.stages.find((candidate) => candidate.stageId === stageId);
  if (!stage) {
    throw new Error(`Stage ${stageId} is unavailable for ${race.caseId}`);
  }
  return stage;
};
