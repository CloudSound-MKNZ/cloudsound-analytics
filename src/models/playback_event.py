"""PlaybackEvent model for analytics service."""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from cloudsound_shared.models.base import Base, UUIDMixin, TimestampMixin
from cloudsound_shared.multitenancy import TenantMixin


class PlaybackEvent(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """PlaybackEvent model for tracking radio playback statistics with tenant isolation."""
    
    __tablename__ = "playback_events"
    
    station_id = Column(UUID(as_uuid=True), ForeignKey("radio_stations.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)  # How long the track was played (null if still playing)
    
    # Composite index for tenant analytics queries
    __table_args__ = (
        Index('ix_playback_events_tenant_timestamp', 'tenant_id', 'timestamp'),
        Index('ix_playback_events_tenant_station', 'tenant_id', 'station_id'),
    )
    
    # Relationships
    station = relationship("RadioStation", back_populates="playback_events")
    track = relationship("Track", back_populates="playback_events")
    
    def __repr__(self) -> str:
        return f"<PlaybackEvent(id={self.id}, station_id={self.station_id}, track_id={self.track_id}, tenant_id={self.tenant_id})>"

