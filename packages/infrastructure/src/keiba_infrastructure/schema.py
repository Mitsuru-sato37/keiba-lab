from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ModelVersion(Base):
    __tablename__ = "model_versions"

    version_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FeatureVersion(Base):
    __tablename__ = "feature_versions"

    version_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    feature_name: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogicVersion(Base):
    __tablename__ = "logic_versions"

    version_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    logic_id: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    batch_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(128), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RawObservation(Base):
    __tablename__ = "raw_observations"

    observation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_record_type: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_record_key: Mapped[str] = mapped_column(String(256), nullable=False)
    source_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    payload_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    ingestion_batch_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DataSnapshot(Base):
    __tablename__ = "data_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    as_of_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_version: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshots"

    feature_snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    horse_id: Mapped[str] = mapped_column(String(128), nullable=False)
    as_of_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_snapshot_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("data_snapshots.snapshot_id"), nullable=False
    )
    feature_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("feature_versions.version_id"), nullable=False
    )
    logic_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("logic_versions.version_id"), nullable=False
    )
    values: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PredictionSnapshot(Base):
    __tablename__ = "prediction_snapshots"

    prediction_snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    as_of_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_snapshot_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("data_snapshots.snapshot_id"), nullable=False
    )
    feature_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("feature_versions.version_id"), nullable=False
    )
    model_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("model_versions.version_id"), nullable=False
    )
    logic_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("logic_versions.version_id"), nullable=False
    )
    predictions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CalculationArtifact(Base):
    __tablename__ = "calculation_artifacts"

    artifact_id: Mapped[str] = mapped_column(String(192), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    lineage: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LogicTrace(Base):
    __tablename__ = "logic_traces"

    trace_id: Mapped[str] = mapped_column(String(192), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_ref_id: Mapped[str] = mapped_column(
        String(192), ForeignKey("calculation_artifacts.artifact_id"), nullable=False
    )
    input_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    data_snapshot_id: Mapped[str] = mapped_column(String(128), nullable=False)
    feature_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    logic_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error: Mapped[str | None] = mapped_column(String(512))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Simulation(Base):
    __tablename__ = "simulations"

    simulation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    logic_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    simulation_result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("simulations.simulation_id"), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    odds_snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    as_of_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(32), nullable=False)
    odds: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    data_snapshot_id: Mapped[str] = mapped_column(String(128), nullable=False)
    logic_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BetCandidate(Base):
    __tablename__ = "bet_candidates"

    candidate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    prediction_snapshot_id: Mapped[str] = mapped_column(String(128), nullable=False)
    odds_snapshot_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("odds_snapshots.odds_snapshot_id"), nullable=False
    )
    bet_type: Mapped[str] = mapped_column(String(32), nullable=False)
    combination: Mapped[str] = mapped_column(String(128), nullable=False)
    model_probability: Mapped[float] = mapped_column(Float, nullable=False)
    odds: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    logic_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    recommendation_item_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    recommendation_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("recommendations.recommendation_id"), nullable=False
    )
    candidate_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("bet_candidates.candidate_id"), nullable=False
    )
    stake_yen: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recommendation_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("recommendations.recommendation_id"), nullable=False
    )
    prediction_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    betting_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    odds_coverage_status: Mapped[str] = mapped_column(String(32), nullable=False)
    logic_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint("decision IN ('BUY', 'SKIP')", name="ck_recommendation_decision"),
    )

    recommendation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(8), nullable=False)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    data_snapshot_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("data_snapshots.snapshot_id"), nullable=False
    )
    prediction_snapshot_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("prediction_snapshots.prediction_snapshot_id"), nullable=False
    )
    feature_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("feature_versions.version_id"), nullable=False
    )
    model_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("model_versions.version_id"), nullable=False
    )
    logic_version_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("logic_versions.version_id"), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Result(Base):
    __tablename__ = "results"

    result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    race_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recommendation_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("recommendations.recommendation_id"), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'invalid')",
            name="ck_backtest_run_status",
        ),
    )

    run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    manifest_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestFold(Base):
    __tablename__ = "backtest_folds"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'invalid')",
            name="ck_backtest_fold_status",
        ),
    )

    fold_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("backtest_runs.run_id"), nullable=False
    )
    test_year: Mapped[int] = mapped_column(Integer, nullable=False)
    training_years: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    manifest_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestGuardResult(Base):
    __tablename__ = "backtest_guard_results"
    __table_args__ = (
        CheckConstraint("status IN ('pass', 'fail')", name="ck_backtest_guard_status"),
    )

    guard_result_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("backtest_runs.run_id"), nullable=False
    )
    fold_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("backtest_folds.fold_id")
    )
    guard_id: Mapped[str] = mapped_column(String(128), nullable=False)
    guard_version: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    checked_input_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestArtifact(Base):
    __tablename__ = "backtest_artifacts"

    artifact_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("backtest_runs.run_id"), nullable=False
    )
    fold_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("backtest_folds.fold_id")
    )
    artifact_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_ref_id: Mapped[str] = mapped_column(String(128), nullable=False)
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
