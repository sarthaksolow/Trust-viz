# Seller Behavior Analyzer Service

A microservice for analyzing seller behavior and detecting potential fraud or suspicious activities in e-commerce platforms.

## Features

- **Account Age Analysis**: Identifies new or recently created seller accounts
- **Growth Rate Analysis**: Detects unusually high product listing rates
- **Description Reuse Detection**: Identifies duplicate or highly similar product descriptions
- **Complaint & Refund Analysis**: Evaluates seller performance based on complaints and refund rates
- **Risk Scoring**: Provides a comprehensive risk score based on multiple behavioral factors
- **Kafka Integration**: Consumes seller events and produces trust events

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
Analyze a seller's behavior.

**Request Body**:
```json
{
  "seller_id": "seller123",
  "seller_name": "Example Seller",
  "account_created_at": "2023-01-01T00:00:00Z",
  "first_listing_date": "2023-01-05T00:00:00Z",
  "total_orders": 100,
  "total_sales": 5000.0,
  "products": [
    {
      "product_id": "prod1",
      "title": "Example Product",
      "description": "This is a sample product description.",
      "created_at": "2023-01-10T00:00:00Z",
      "price": 49.99,
      "category": "electronics",
      "is_high_risk": false
    }
  ],
  "complaints": [
    {
      "complaint_id": "comp1",
      "type": "medium",
      "description": "Item not as described",
      "created_at": "2023-02-15T00:00:00Z",
      "result": "refunded"
    }
  ],
  "metadata": {}
}
```

**Response**:
```json
{
  "seller_id": "seller123",
  "behavior_score": 0.75,
  "risk_level": "low",
  "is_high_risk": false,
  "components": {
    "account_age": 0.85,
    "growth_rate": 0.9,
    "description_reuse": 0.95,
    "complaint_analysis": 0.7
  },
  "analysis_timestamp": "2023-03-01T12:00:00.123456"
}
```

## Kafka Integration

### Consumed Topics
- `seller-events`: Incoming seller data to be analyzed

### Produced Topics
- `trust-events`: Events generated for high-risk sellers

## Configuration

The following environment variables can be used to configure the service:

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka bootstrap servers | `kafka:29093` |
| `KAFKA_TOPIC_SELLER_EVENTS` | Topic for incoming seller events | `seller-events` |
| `KAFKA_GROUP_ID` | Consumer group ID | `seller-analyzer-group` |
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
   cd services/seller-behavior-analyzer
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
docker build -t seller-behavior-analyzer .
```

## Architecture

The service uses a weighted scoring system to evaluate seller trustworthiness:

```
behavior_score = 0.2 * account_age_score + 
                0.3 * growth_rate_score + 
                0.2 * description_reuse_score + 
                0.3 * complaint_analysis_score
```

- **Account Age (20%)**: Newer accounts are considered higher risk
- **Growth Rate (30%)**: Rapidly growing product catalogs may indicate fraudulent behavior
- **Description Reuse (20%)**: Duplicate descriptions across products may indicate low-quality listings
- **Complaint Analysis (30%)**: High complaint and refund rates negatively impact the score

## License

MIT
