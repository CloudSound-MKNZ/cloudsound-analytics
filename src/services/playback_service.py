"""Playback event service for tracking radio playback statistics."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from ..models import PlaybackEvent
from cloudsound_shared.logging import get_logger

logger = get_logger(__name__)


class PlaybackEventService:
    """Service for managing playback events."""
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
    
    async def create_playback_event(
        self,
        station_id: UUID,
        track_id: UUID,
        duration_seconds: Optional[int] = None
    ) -> PlaybackEvent:
        """Create a new playback event."""
        event = PlaybackEvent(
            station_id=station_id,
            track_id=track_id,
            timestamp=datetime.utcnow(),
            duration_seconds=duration_seconds
        )
        
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        logger.info(
            "playback_event_created",
            event_id=str(event.id),
            station_id=str(station_id),
            track_id=str(track_id),
            duration_seconds=duration_seconds
        )
        
        return event
    
    async def get_playback_events_by_station(
        self,
        station_id: UUID,
        limit: int = 100
    ) -> List[PlaybackEvent]:
        """Get playback events for a station."""
        query = select(PlaybackEvent).where(PlaybackEvent.station_id == station_id)
        query = query.order_by(PlaybackEvent.timestamp.desc())
        query = query.limit(limit)
        query = query.options(
            selectinload(PlaybackEvent.station),
            selectinload(PlaybackEvent.track)
        )
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        logger.info("retrieved_playback_events", station_id=str(station_id), count=len(events))
        return list(events)
    
    async def get_playback_events_by_track(
        self,
        track_id: UUID,
        limit: int = 100
    ) -> List[PlaybackEvent]:
        """Get playback events for a track."""
        query = select(PlaybackEvent).where(PlaybackEvent.track_id == track_id)
        query = query.order_by(PlaybackEvent.timestamp.desc())
        query = query.limit(limit)
        query = query.options(
            selectinload(PlaybackEvent.station),
            selectinload(PlaybackEvent.track)
        )
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        logger.info("retrieved_playback_events_by_track", track_id=str(track_id), count=len(events))
        return list(events)
    
    async def get_playback_statistics(
        self,
        station_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get aggregated playback statistics."""
        query = select(
            func.count(PlaybackEvent.id).label("total_plays"),
            func.sum(PlaybackEvent.duration_seconds).label("total_duration")
        )
        
        if station_id:
            query = query.where(PlaybackEvent.station_id == station_id)
        
        if start_date:
            query = query.where(PlaybackEvent.timestamp >= start_date)
        
        if end_date:
            query = query.where(PlaybackEvent.timestamp <= end_date)
        
        result = await self.db.execute(query)
        stats = result.first()
        
        statistics = {
            "total_plays": stats.total_plays or 0,
            "total_duration_seconds": stats.total_duration or 0
        }
        
        logger.info("retrieved_playback_statistics", **statistics)
        return statistics

