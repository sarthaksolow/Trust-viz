import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from confluent_kafka import Producer, Consumer, KafkaError
import json

from services.review_analyzer.analyzer import ReviewAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review-analyzer")

# Initialize FastAPI app
app = FastAPI(
    title="Review Analyzer Service",
    description="Microservice for analyzing review authenticity",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the analyzer
analyzer = ReviewAnalyzer()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
KAFKA_TOPIC_REVIEWS = os.getenv("KAFKA_TOPIC_REVIEWS", "product-reviews")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "review-analyzer-group")
KAFKA_TOPIC_TRUST_EVENTS = os.getenv("KAFKA_TOPIC_TRUST_EVENTS", "trust-events")

# Kafka producer for trust events
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'review-analyzer-producer'
})

def delivery_report(err, msg):
    """Callback for Kafka produce delivery reports."""
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Pydantic models
class Review(BaseModel):
    review_id: str
    text: str
    reviewer_id: str
    product_id: str
    timestamp: str
    is_verified: bool = False
    rating: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    review_id: str
    authenticity_score: float
    is_suspicious: bool
    components: Dict[str, float]
    analysis_timestamp: str

class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: str

# API Endpoints
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_review(review: Review):
    """
    Analyze a single review for authenticity.
    
    This endpoint accepts a review and returns an authenticity analysis.
    """
    try:
        # Convert Pydantic model to dict for processing
        review_data = review.dict()
        
        # Perform analysis
        result = analyzer.analyze_review(review_data)
        
        # Publish trust event if suspicious
        if result['is_suspicious']:
            trust_event = {
                'event_type': 'suspicious_review',
                'review_id': review.review_id,
                'reviewer_id': review.reviewer_id,
                'product_id': review.product_id,
                'score': result['authenticity_score'],
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    'components': result['components'],
                    'service': 'review-analyzer'
                }
            }
            
            producer.produce(
                topic=KAFKA_TOPIC_TRUST_EVENTS,
                key=review.review_id.encode('utf-8'),
                value=json.dumps(trust_event).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def consume_reviews():
    """Consume reviews from Kafka and analyze them."""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest'
    })
    
    consumer.subscribe([KAFKA_TOPIC_REVIEWS])
    
    logger.info(f"Started consuming messages from {KAFKA_TOPIC_REVIEWS}")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    continue
            
            try:
                # Process the message
                review_data = json.loads(msg.value().decode('utf-8'))
                logger.info(f"Processing review: {review_data.get('review_id')}")
                
                # Analyze the review
                result = analyzer.analyze_review(review_data)
                
                # Publish trust event if suspicious
                if result['is_suspicious']:
                    trust_event = {
                        'event_type': 'suspicious_review',
                        'review_id': review_data['review_id'],
                        'reviewer_id': review_data['reviewer_id'],
                        'product_id': review_data['product_id'],
                        'score': result['authenticity_score'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {
                            'components': result['components'],
                            'service': 'review-analyzer'
                        }
                    }
                    
                    producer.produce(
                        topic=KAFKA_TOPIC_TRUST_EVENTS,
                        key=review_data['review_id'].encode('utf-8'),
                        value=json.dumps(trust_event).encode('utf-8'),
                        callback=delivery_report
                    )
                    producer.flush()
                
                # Commit the message offset
                consumer.commit(msg)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to decode message: {msg.value()}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                
    except KeyboardInterrupt:
        pass
    finally:
        # Close down consumer and producer to commit final offsets.
        consumer.close()
        producer.flush()

if __name__ == "__main__":
    import asyncio
    import threading
    
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=asyncio.run, args=(consume_reviews(),))
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Start the FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5004,
        log_level="info",
        reload=True
    )
