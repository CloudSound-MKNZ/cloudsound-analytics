"""PlaybackEvent model for analytics service."""
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from cloudsound_shared.models.base import Base, UUIDMixin


class PlaybackEvent(Base, UUIDMixin):
    """PlaybackEvent model for tracking radio playback statistics."""
    
    __tablename__ = "playback_events"
    
    station_id = Column(UUID(as_uuid=True), ForeignKey("radio_stations.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)  # How long the track was played (null if still playing)
    
    # Relationships
    station = relationship("RadioStation", back_populates="playback_events")
    track = relationship("Track", back_populates="playback_events")
    
    def __repr__(self) -> str:
        return f"<PlaybackEvent(id={self.id}, station_id={self.station_id}, track_id={self.track_id}, timestamp={self.timestamp})>"

