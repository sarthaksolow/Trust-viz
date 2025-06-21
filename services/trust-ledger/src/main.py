from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from confluent_kafka import Consumer
from blockchain import Blockchain  # Make sure this exists
import os
import json
import time

# Set up Kafka config first
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_TRUST_EVENTS = os.getenv("KAFKA_TOPIC_TRUST_EVENTS", "trust-events")

consumer_config = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "trust-ledger-consumer",
    "auto.offset.reset": "earliest"
}

# Retry logic
def init_consumer_with_retry():
    from confluent_kafka import KafkaException
    retries = 5
    for attempt in range(retries):
        try:
            consumer = Consumer(consumer_config)
            consumer.subscribe([KAFKA_TOPIC_TRUST_EVENTS])
            print("✅ Kafka connected successfully.")
            return consumer
        except KafkaException as e:
            print(f"❌ Kafka connection failed. Retrying in 5s... ({attempt+1}/{retries})")
            time.sleep(5)
    raise RuntimeError("Failed to connect to Kafka after retries.")

# Initialize
consumer = init_consumer_with_retry()
ledger = Blockchain()
app = FastAPI()  # ⛔ Don't declare this after endpoints

# ----------------------
# ROUTES
# ----------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "chain_length": len(ledger.chain),
        "service": "Trust Ledger"
    }

@app.get("/ledger")
def get_ledger():
    return ledger.get_chain()

# ----------------------
# KAFKA Polling
# ----------------------

@app.on_event("startup")
@repeat_every(seconds=5)
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
            print(f"💾 Writing to Trust Ledger: product {event.get('product_id')} with score {event.get('trust_score')}")
            ledger.add_block(event)
        except Exception as e:
            print(f"⚠️ Error processing message: {e}")
