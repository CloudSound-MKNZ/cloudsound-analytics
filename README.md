# Analytics Service

Tracks playback events and aggregates statistics.

## Features

- Playback event tracking
- Statistics aggregation
- Kafka consumer for playback events
- gRPC server for playback event streaming

## Development

```bash
cd backend/analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8007
```

