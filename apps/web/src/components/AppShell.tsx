import { useState } from "react";
import {
  GOLDEN_STAGE_ORDER,
  getGoldenRaceCase,
  goldenRaceCases,
  type GoldenRaceCase,
  type GoldenStageId,
} from "../goldenRaceFixture";
import { LogicExplorerView } from "./LogicExplorerView";
import { RaceView } from "./RaceView";
import { TodayView } from "./TodayView";

type AppView = "today" | "race" | "logic";

export function AppShell() {
  const [view, setView] = useState<AppView>("today");
  const [selectedCaseId, setSelectedCaseId] =
    useState<GoldenRaceCase["caseId"]>(goldenRaceCases[0].caseId);
  const [selectedStageId, setSelectedStageId] =
    useState<GoldenStageId>(GOLDEN_STAGE_ORDER[0]);
  const selectedRace = getGoldenRaceCase(selectedCaseId);
  const safeStageId = selectedRace.stages.some(
    (stage) => stage.stageId === selectedStageId,
  )
    ? selectedStageId
    : selectedRace.stages[0].stageId;

  const selectRace = (caseId: GoldenRaceCase["caseId"]) => {
    setSelectedCaseId(caseId);
    setSelectedStageId(GOLDEN_STAGE_ORDER[0]);
    setView("race");
  };

  if (view === "today") {
    return (
      <main className="app-shell">
        <TodayView cases={goldenRaceCases} onSelectRace={selectRace} />
      </main>
    );
  }

  if (view === "race") {
    return (
      <main className="app-shell">
        <RaceView
          race={selectedRace}
          onBack={() => setView("today")}
          onExploreStage={(stageId) => {
            setSelectedStageId(stageId);
            setView("logic");
          }}
        />
      </main>
    );
  }

  return (
    <main className="app-shell">
      <LogicExplorerView
        race={selectedRace}
        stageId={safeStageId}
        onBack={() => setView("race")}
        onSelectStage={setSelectedStageId}
      />
    </main>
  );
}
