# data_ingestion/producer.py
from confluent_kafka import Producer
import json

# Point to your Kafka broker (from Docker Compose)
producer = Producer({
    'bootstrap.servers': 'trustviz-kafka-1:9092'  # Adjust if needed
})

def send_to_kafka(data: dict):
    try:
        producer.produce('raw-data', value=json.dumps(data))
        producer.flush()
        print("✅ Data sent to Kafka topic 'raw-data'")
    except Exception as e:
        print(f"❌ Failed to send data to Kafka: {e}")
