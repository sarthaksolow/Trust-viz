# To run this server, use the following command:
# uvicorn main:app --host 0.0.0.0 --port 8004 --reload

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi_utils.tasks import repeat_every
from confluent_kafka import Consumer
import os
import json

class SellerAction(BaseModel):
    seller_id: str
    action: str
    timestamp: str

app = FastAPI()

@app.post("/record")
async def record_transaction(action: SellerAction):
    print(f"📝 Received manual transaction: {action.dict()}")
    return {"transaction_id": "0xabc...", "status": "recorded"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "Trust Ledger"
    }

# Kafka Setup
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_TRUST_EVENTS = os.getenv("KAFKA_TOPIC_TRUST_EVENTS", "trust-events")

consumer_config = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "trust-ledger-consumer",
    "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)
consumer.subscribe([KAFKA_TOPIC_TRUST_EVENTS])

@app.on_event("startup")
@repeat_every(seconds=5)  # Poll Kafka every 5 seconds
def consume_trust_events():
    msg = consumer.poll(1.0)
    if msg is None:
        return
    if msg.error():
        print(f"❌ Kafka error: {msg.error()}")
    else:
        try:
            event = json.loads(msg.value())
            print(f"📥 Received from Kafka (trust-events): {event}")
            # Simulate saving to ledger
            print(f"💾 Writing to Trust Ledger: product {event.get('product_id')} with score {event.get('trust_score')}")
        except Exception as e:
            print(f"⚠️ Error processing message: {e}")
