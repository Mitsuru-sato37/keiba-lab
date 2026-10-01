from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String
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
