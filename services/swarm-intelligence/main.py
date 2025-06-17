# To run the server, use:
# uvicorn main:app --host 0.0.0.0 --port 5001 --reload
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from confluent_kafka import Producer, Consumer, KafkaException
from fastapi_utils.tasks import repeat_every
import json
import os
import logging

# ----------------------------------
# Logging setup
# ----------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmIntelligence")

# ----------------------------------
# FastAPI App
# ----------------------------------
app = FastAPI(title="Swarm Intelligence")

# ----------------------------------
# Kafka Config
# ----------------------------------
KAFKA_BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC_RAW_DATA = os.getenv('KAFKA_TOPIC_RAW_DATA', 'raw-data')
KAFKA_TOPIC_IMAGE_CHECK = os.getenv('KAFKA_TOPIC_IMAGE_CHECK', 'image-check')
KAFKA_TOPIC_IMAGE_SCORE = os.getenv('KAFKA_TOPIC_IMAGE_SCORE', 'image-score')
KAFKA_TOPIC_TRUST_EVENTS = os.getenv('KAFKA_TOPIC_TRUST_EVENTS', 'trust-events')

producer = None
consumer = None

# ----------------------------------
# Kafka Helpers
# ----------------------------------
def get_producer_config():
    return {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'client.id': 'swarm-intelligence-producer'
    }

def get_consumer_config():
    return {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'swarm-intelligence-group',
        'auto.offset.reset': 'earliest'
    }

def delivery_report(err, msg):
    if err is not None:
        logger.error(f'❌ Message delivery failed: {err}')
    else:
        logger.info(f'✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

# ----------------------------------
# FastAPI Startup & Shutdown
# ----------------------------------
@app.on_event("startup")
def startup_event():
    global producer, consumer
    logger.info("🚀 Starting Swarm Intelligence Service...")

    try:
        producer = Producer(get_producer_config())
        logger.info("✅ Kafka Producer initialized.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize producer: {e}")
        raise

    try:
        consumer = Consumer(get_consumer_config())
        consumer.subscribe([KAFKA_TOPIC_RAW_DATA])
        logger.info("✅ Kafka Consumer subscribed to 'raw-data'.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize consumer: {e}")
        raise

@app.on_event("shutdown")
def shutdown_event():
    if producer:
        producer.flush()
        logger.info("🧼 Kafka Producer flushed.")
    if consumer:
        consumer.close()
        logger.info("🧼 Kafka Consumer closed.")

# ----------------------------------
# Manual Analysis Endpoint
# ----------------------------------
class AnalysisRequest(BaseModel):
    data: Dict[Any, Any]

@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    try:
        data = request.data
        logger.info(f"🧪 Manual analysis triggered: {data}")

        producer.produce(
            KAFKA_TOPIC_IMAGE_CHECK,
            key=data.get('product_id', '').encode('utf-8'),
            value=json.dumps(data).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()

        return {"fraud_score": 0.1, "agent_id": "agent-001"}
    except Exception as e:
        logger.error(f"❌ Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Swarm Intelligence",
        "kafka_connected": producer is not None
    }

# ----------------------------------
# Background Task: Poll raw-data topic
# ----------------------------------
@app.on_event("startup")
@repeat_every(seconds=2)
def poll_raw_data():
    global consumer
    try:
        msg = consumer.poll(1.0)
        if msg is None:
            return
        if msg.error():
            raise KafkaException(msg.error())

        raw_event = json.loads(msg.value().decode('utf-8'))
        logger.info(f"📥 Received raw event: {raw_event}")

        # Simple rule-based scoring
        risk_score = 0.1 if raw_event.get("quantity", 0) < 100 else 0.9

        # 1. Image check request
        image_payload = {
            "product_id": raw_event["product_id"],
            "product_image_url": raw_event.get("product_image_url", "")
        }
        producer.produce(
            KAFKA_TOPIC_IMAGE_CHECK,
            key=raw_event["product_id"],
            value=json.dumps(image_payload).encode('utf-8'),
            callback=delivery_report
        )

        # 2. Trust events (early)
        trust_payload = {
            "seller_id": raw_event["seller_id"],
            "product_id": raw_event["product_id"],
            "risk_score": risk_score,
            "stage": "early"
        }
        producer.produce(
            KAFKA_TOPIC_TRUST_EVENTS,
            key=raw_event["seller_id"],
            value=json.dumps(trust_payload).encode('utf-8'),
            callback=delivery_report
        )

        producer.flush()
    except Exception as e:
        logger.error(f"🚨 Error during raw-data polling: {e}")
