# To run this server, use the following command:
# uvicorn main:app --host 0.0.0.0 --port 5002 --reload

from fastapi import FastAPI, Request
from confluent_kafka import Consumer, Producer
import json
import os
from fastapi.exceptions import HTTPException

app = FastAPI()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC_IMAGE_CHECK = os.getenv('KAFKA_TOPIC_IMAGE_CHECK', 'image-check')
KAFKA_TOPIC_IMAGE_SCORE = os.getenv('KAFKA_TOPIC_IMAGE_SCORE', 'image-score')

# Initialize Kafka producer
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'perceptual-ai-producer'
})

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

@app.post("/analyze")
async def analyze(request: Request):
    try:
        data = await request.json()
        print(f"Received data for analysis: {data}")
        
        # Process the image data (placeholder)
        visual_match_score = 0.95  # This should be replaced with actual AI processing
        is_ai_generated = False    # This should be replaced with actual AI processing
        
        # Send score back to swarm intelligence
        producer.produce(
            KAFKA_TOPIC_IMAGE_SCORE,
            key=data.get('product_id', '').encode('utf-8'),
            value=json.dumps({
                'product_id': data.get('product_id'),
                'visual_match_score': visual_match_score,
                'is_ai_generated': is_ai_generated
            }).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()
        
        return {
            "visual_match_score": visual_match_score,
            "is_ai_generated": is_ai_generated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Perceptual AI"}

@app.on_event("shutdown")
async def shutdown_event():
    producer.flush()