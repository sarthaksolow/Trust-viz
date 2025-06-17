# To run this server, use the following command:
# uvicorn main:app --reload

from fastapi import FastAPI, HTTPException
from typing import Any, Dict
from pydantic import BaseModel
from confluent_kafka import Producer
import json
import os

app = FastAPI()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC_RAW_DATA = os.getenv('KAFKA_TOPIC_RAW_DATA', 'raw-data')

# Initialize Kafka producer
def create_kafka_producer():
    config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'client.id': 'data-ingestion-producer'
    }
    return Producer(config)

# Kafka delivery callback
def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

# Initialize producer
producer = create_kafka_producer()

@app.on_event("shutdown")
async def shutdown_event():
    producer.flush()

# Health check endpoint
@app.get("/health")
def health_check():
    try:
        # Try accessing metadata to confirm Kafka connection
        metadata = producer.list_topics(timeout=5)
        kafka_connected = KAFKA_TOPIC_RAW_DATA in metadata.topics
    except Exception as e:
        kafka_connected = False

    return {
        "status": "ok",
        "service": "Data Ingestion",
        "kafka_connected": kafka_connected
    }

# Pydantic model for better validation
class SellerData(BaseModel):
    seller_id: str
    product_id: str
    product_name: str
    quantity: int
    price: float
    product_image_url: str  # Added for image analysis

@app.post("/ingest")
async def ingest_data(data: SellerData):
    try:
        # Convert data to JSON string
        data_json = data.json()

        # Send to raw-data topic
        producer.produce(
            KAFKA_TOPIC_RAW_DATA,
            key=data.seller_id.encode('utf-8'),
            value=data_json.encode('utf-8'),
            callback=delivery_report
        )

        # Force flush to ensure delivery
        producer.flush()

        return {
            "status": "success",
            "message": f"Data received and forwarded to Kafka for product {data.product_id}",
            "data": data.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
