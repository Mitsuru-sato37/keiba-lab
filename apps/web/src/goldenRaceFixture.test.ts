import { describe, expect, it } from "vitest";
import {
  GOLDEN_STAGE_ORDER,
  getGoldenRaceCase,
  getStageEvidence,
  goldenRaceCases,
} from "./goldenRaceFixture";

describe("Golden Race web fixture", () => {
  it("contains reproducible BUY and SKIP cases", () => {
    expect(goldenRaceCases.map((race) => race.caseId)).toEqual([
      "golden-buy",
      "golden-skip",
    ]);
    expect(getGoldenRaceCase("golden-buy").decision).toBe("BUY");
    expect(getGoldenRaceCase("golden-skip").decision).toBe("SKIP");
    expect(getGoldenRaceCase("golden-skip").reasonCodes).toContain(
      "SKIP_NO_VALUE",
    );
    expect(getGoldenRaceCase("golden-buy").reasonCodes).toEqual([]);
  });

  it("preserves the fixed stage order and returns evidence for each stage", () => {
    const race = getGoldenRaceCase("golden-buy");

    expect(race.stages.map((stage) => stage.stageId)).toEqual(
      GOLDEN_STAGE_ORDER,
    );
    expect(getStageEvidence(race, "ability_prediction").label).toBe(
      "Ability prediction",
    );
    expect(getStageEvidence(race, "recommendation").lineage.logicVersion).toBe(
      "LOGIC-REC-001",
    );
  });

  it("keeps optional evidence explicitly unavailable", () => {
    const race = getGoldenRaceCase("golden-skip");
    const earlyStage = getStageEvidence(race, "ability_prediction");

    expect(earlyStage.inputs.find((input) => input.label === "Current-race odds")).toBeUndefined();
    expect(earlyStage.outputs.find((output) => output.label === "Result")?.value).toBeNull();
  });
});
