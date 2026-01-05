"""Kafka consumer for playback events in analytics service."""
import asyncio
from typing import Dict, Any
from uuid import UUID
from cloudsound_shared.kafka import KafkaConsumerClient
from cloudsound_shared.logging import get_logger
from cloudsound_shared.metrics import kafka_messages_consumed
from ..services.playback_service import PlaybackEventService
from cloudsound_shared.db.pool import AsyncSessionLocal

logger = get_logger(__name__)


class PlaybackEventConsumer:
    """Consumer for playback events from Kafka."""
    
    def __init__(self):
        """Initialize the consumer."""
        self.consumer = KafkaConsumerClient(
            topics=["radio.playback.events"],
            group_id="analytics-playback-consumer",
            auto_offset_reset="earliest"
        )
        self.running = False
        self.loop = None
    
    async def process_message(self, message: Dict[Any, Any]) -> None:
        """Process a single playback event message."""
        try:
            station_id = UUID(message["station_id"])
            track_id = UUID(message["track_id"])
            duration_seconds = message.get("duration_seconds")
            
            # Create playback event in database
            async with AsyncSessionLocal() as session:
                service = PlaybackEventService(session)
                await service.create_playback_event(
                    station_id=station_id,
                    track_id=track_id,
                    duration_seconds=duration_seconds
                )
            
            # Update metrics
            kafka_messages_consumed.labels(
                topic="radio.playback.events",
                group_id="analytics-playback-consumer"
            ).inc()
            
            logger.info(
                "playback_event_processed",
                station_id=str(station_id),
                track_id=str(track_id),
                duration_seconds=duration_seconds
            )
        
        except Exception as e:
            logger.error(
                "playback_event_processing_failed",
                message=message,
                error=str(e),
                exc_info=True
            )
            # Continue processing other messages even if one fails
    
    def _process_sync(self, message_value: Dict[Any, Any]) -> None:
        """Process message synchronously by running async function."""
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        self.loop.run_until_complete(self.process_message(message_value))
    
    def start(self) -> None:
        """Start consuming messages from Kafka."""
        self.running = True
        self.consumer.connect()
        
        logger.info("playback_consumer_started")
        
        try:
            for message in self.consumer.consume():
                if not self.running:
                    break
                
                # Process message (synchronously, but calls async function)
                self._process_sync(message.value)
        
        except KeyboardInterrupt:
            logger.info("playback_consumer_stopping")
        except Exception as e:
            logger.error("playback_consumer_error", error=str(e), exc_info=True)
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop consuming messages."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.loop:
            self.loop.close()
        logger.info("playback_consumer_stopped")


# Global consumer instance
_consumer: PlaybackEventConsumer = None


def get_consumer() -> PlaybackEventConsumer:
    """Get or create consumer instance."""
    global _consumer
    if _consumer is None:
        _consumer = PlaybackEventConsumer()
    return _consumer

