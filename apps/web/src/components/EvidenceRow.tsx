import type { EvidenceValue } from "../goldenRaceFixture";

type EvidenceRowProps = {
  label: string;
  value: EvidenceValue;
};

export function EvidenceRow({ label, value }: EvidenceRowProps) {
  return (
    <div className="evidence-row">
      <dt>{label}</dt>
      <dd>{value === null ? "未提供" : String(value)}</dd>
    </div>
  );
}
