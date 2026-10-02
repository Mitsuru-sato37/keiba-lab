export type ValidationRunner = {
  runnerId: string;
  gate: number;
  winProbability: number;
  finishPosition: number;
};

export type ValidationRace = {
  raceId: string;
  targetDate: string;
  asOfTime: string;
  trainingWindow: string;
  decision: "BUY" | "SKIP";
  recommendationPersisted: boolean;
  winnerId: string;
  winPayoutYen: number;
  runners: readonly ValidationRunner[];
};

export const firstValidationRace: ValidationRace = {
  raceId: "validation-2022-0105-r01",
  targetDate: "2022-01-05",
  asOfTime: "2022-01-05T01:00:00Z",
  trainingWindow: "2019–2021",
  decision: "BUY",
  recommendationPersisted: true,
  winnerId: "validation-2022-0105-r01-h01",
  winPayoutYen: 280,
  runners: [
    {
      runnerId: "validation-2022-0105-r01-h01",
      gate: 1,
      winProbability: 2 / 3,
      finishPosition: 1,
    },
    {
      runnerId: "validation-2022-0105-r01-h02",
      gate: 2,
      winProbability: 1 / 3,
      finishPosition: 2,
    },
  ],
};
