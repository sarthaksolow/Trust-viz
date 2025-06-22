# Review Analyzer Service

A microservice for detecting fake and suspicious product reviews using machine learning and pattern analysis.

## Features

- **Text Uniqueness Analysis**: Detects duplicate or near-duplicate reviews
- **Temporal Analysis**: Identifies review bursts and suspicious timing patterns
- **Verification Check**: Considers purchase verification status
- **Sentiment Analysis**: Detects overly positive/negative sentiment patterns
- **Kafka Integration**: Consumes review events and produces trust events

## API Endpoints

### `GET /health`
Check service health.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2023-01-01T00:00:00.000000"
}
```

### `POST /analyze`
Analyze a review for authenticity.

**Request Body**:
```json
{
  "review_id": "review123",
  "text": "Great product! Works as expected.",
  "reviewer_id": "user123",
  "product_id": "prod456",
  "timestamp": "2023-01-01T00:00:00Z",
  "is_verified": true,
  "rating": 5,
  "metadata": {}
}
```

**Response**:
```json
{
  "review_id": "review123",
  "authenticity_score": 0.85,
  "is_suspicious": false,
  "components": {
    "uniqueness": 0.9,
    "temporal": 0.8,
    "verified": 1.0,
    "sentiment": 0.6
  },
  "analysis_timestamp": "2023-01-01T00:00:00.123456"
}
```

## Kafka Integration

### Consumed Topics
- `product-reviews`: Incoming product reviews to be analyzed

### Produced Topics
- `trust-events`: Events generated for suspicious reviews

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers | `kafka:29092` |
| `KAFKA_TOPIC_REVIEWS` | Topic for incoming reviews | `product-reviews` |
| `KAFKA_GROUP_ID` | Consumer group ID | `review-analyzer-group` |
| `KAFKA_TOPIC_TRUST_EVENTS` | Topic for trust events | `trust-events` |

## Development

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Kafka (included in docker-compose)

### Setup

1. Clone the repository
2. Navigate to the service directory:
   ```bash
   cd services/review-analyzer
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Running Tests

```bash
pytest tests/
```

### Running Locally

1. Start Kafka and dependencies:
   ```bash
   docker-compose up -d kafka zookeeper
   ```

2. Run the service:
   ```bash
   python -m src.main
   ```

### Building the Docker Image

```bash
docker build -t review-analyzer .
```

## Architecture

The service uses a weighted scoring system to evaluate review authenticity:

```
review_score = 0.4 * uniqueness + 0.3 * timestamp_check + 0.2 * verified_ratio + 0.1 * sentiment_score
```

- **Uniqueness (40%)**: Measures how unique the review text is compared to others
- **Temporal (30%)**: Checks for suspicious timing patterns (e.g., review bursts)
- **Verified (20%)**: Considers if the review is from a verified purchase
- **Sentiment (10%)**: Analyzes sentiment patterns that might indicate fake reviews

## License

MIT
