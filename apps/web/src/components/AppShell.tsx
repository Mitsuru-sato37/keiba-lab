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

type ProductNavigationProps = {
  view: AppView;
  onNavigate: (view: AppView) => void;
};

function ProductNavigation({ view, onNavigate }: ProductNavigationProps) {
  return (
    <nav aria-label="Product navigation" className="app-navigation">
      {([
        ["today", "Today"],
        ["race", "Race"],
        ["logic", "Logic Explorer"],
      ] as const).map(([target, label]) => (
        <button
          aria-current={view === target ? "page" : undefined}
          key={target}
          onClick={() => onNavigate(target)}
          type="button"
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

function Shell({ view, onNavigate, children }: ProductNavigationProps & { children: React.ReactNode }) {
  return (
    <main className="app-shell">
      <ProductNavigation view={view} onNavigate={onNavigate} />
      {children}
    </main>
  );
}

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
      <Shell view={view} onNavigate={setView}>
        <TodayView cases={goldenRaceCases} onSelectRace={selectRace} />
      </Shell>
    );
  }

  if (view === "race") {
    return (
      <Shell view={view} onNavigate={setView}>
        <RaceView
          race={selectedRace}
          onBack={() => setView("today")}
          onExploreStage={(stageId) => {
            setSelectedStageId(stageId);
            setView("logic");
          }}
        />
      </Shell>
    );
  }

  return (
    <Shell view={view} onNavigate={setView}>
      <LogicExplorerView
        race={selectedRace}
        stageId={safeStageId}
        onBack={() => setView("race")}
        onSelectStage={setSelectedStageId}
      />
    </Shell>
  );
}
