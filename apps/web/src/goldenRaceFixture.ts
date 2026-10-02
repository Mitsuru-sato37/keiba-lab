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
  data_snapshot: "データスナップショット",
  feature_snapshot: "特徴量スナップショット",
  ability_prediction: "能力予測",
  calibration: "確率補正",
  simulation: "仮想レースシミュレーション",
  bet_probability: "馬券確率",
  odds_snapshot: "オッズスナップショット",
  expected_value: "期待値",
  strategy: "買い方の判定",
  money_allocation: "資金配分",
  recommendation: "最終判定",
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
        { label: "レーススナップショット", value: `snapshot-${caseId}` },
        { label: "馬場", value: surface === "turf" ? "芝" : "ダート" },
      ],
      conditions: [
        "予想時点までに受け取ったデータだけを使用",
        isMarketStage
          ? "市場情報は予想保存後に評価"
          : "能力予測には当該レースのオッズを使用しない",
      ],
      outputs: [
        { label: "ステップ状態", value: "成功" },
        { label: "結果", value: null },
        { label: "払戻", value: null },
      ],
      lineage: sharedLineage(caseId, stageId),
      validationReferences: ["LEAK-001", "VERSION-001"],
    };

    if (stageId === "ability_prediction") {
      stage.inputs.push({ label: "走力スコアの特徴量", value: "3頭" });
      stage.outputs.push({ label: "上位候補", value: "horse-1 / horse-4" });
    }

    if (stageId === "odds_snapshot") {
      stage.inputs.push({ label: "当該レースのオッズ", value: "2.8 / 4.0 / 8.0" });
      stage.outputs.push({ label: "オッズ受信時刻", value: "2022-01-01 09:30 UTC" });
    }

    if (stageId === "recommendation") {
      stage.outputs.push({ label: "判定", value: decision === "BUY" ? "購入" : "見送り" });
      stage.outputs.push({
        label: "理由",
        value: decision === "BUY" ? "市場価値あり" : "市場価値なし（SKIP_NO_VALUE）",
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
  dataStatus: "判定まで完了。結果と払戻は保存条件により管理",
  calculatedAt: "2022-01-01T09:35:00Z",
  strategies: [
    {
      name: "Stable",
      decision,
      candidateCount: decision === "BUY" ? 1 : 0,
      stake: decision === "BUY" ? 200 : 0,
      explanation:
        decision === "BUY" ? "安定型の投資上限内で市場価値あり" : "許容できる市場価値なし",
    },
    {
      name: "Balanced",
      decision,
      candidateCount: decision === "BUY" ? 1 : 0,
      stake: decision === "BUY" ? 300 : 0,
      explanation:
        decision === "BUY" ? "価値と信頼度がバランス型の基準を超過" : "価値の基準未達",
    },
    {
      name: "Longshot",
      decision: "SKIP",
      candidateCount: 0,
      stake: 0,
      explanation: "この検証データでは穴狙いの候補なし",
    },
  ],
  stages: createStages(caseId, surface, decision),
});

export const goldenRaceCases: readonly GoldenRaceCase[] = [
  makeCase("golden-buy", "golden-race-buy", "ゴールデンレース（購入）", "turf", 1600, "BUY"),
  makeCase("golden-skip", "golden-race-skip", "ゴールデンレース（見送り）", "dirt", 1400, "SKIP"),
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
