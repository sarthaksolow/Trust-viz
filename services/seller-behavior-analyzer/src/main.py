import os
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uvicorn
from confluent_kafka import Producer, Consumer, KafkaError
import json

from services.seller_behavior_analyzer.analyzer import SellerBehaviorAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seller-behavior-analyzer")

# Initialize FastAPI app
app = FastAPI(
    title="Seller Behavior Analyzer Service",
    description="Microservice for analyzing seller behavior and detecting potential fraud",
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
analyzer = SellerBehaviorAnalyzer()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29093")
KAFKA_TOPIC_SELLER_EVENTS = os.getenv("KAFKA_TOPIC_SELLER_EVENTS", "seller-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "seller-analyzer-group")
KAFKA_TOPIC_TRUST_EVENTS = os.getenv("KAFKA_TOPIC_TRUST_EVENTS", "trust-events")

# Kafka producer for trust events
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'seller-analyzer-producer'
})

def delivery_report(err, msg):
    """Callback for Kafka produce delivery reports."""
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

# Pydantic models
class Product(BaseModel):
    product_id: str
    title: str
    description: str
    created_at: str
    price: float
    category: str
    is_high_risk: bool = False

class Complaint(BaseModel):
    complaint_id: str
    type: str  # 'low', 'medium', 'high', 'fraud', 'scam'
    description: str
    created_at: str
    result: Optional[str] = None  # 'refunded', 'resolved', 'pending', etc.


class SellerData(BaseModel):
    seller_id: str
    seller_name: str
    account_created_at: str
    first_listing_date: Optional[str] = None
    total_orders: int = 0
    total_sales: float = 0.0
    products: List[Product] = []
    complaints: List[Complaint] = []
    metadata: Dict[str, Any] = {}

class AnalysisResult(BaseModel):
    seller_id: str
    behavior_score: float
    risk_level: str
    is_high_risk: bool
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
async def analyze_seller(seller_data: SellerData):
    """
    Analyze a seller's behavior and return a trust score.
    """
    try:
        # Convert Pydantic model to dict for processing
        seller_dict = seller_data.dict()
        
        # Perform analysis
        result = analyzer.analyze_seller(seller_dict)
        
        # Publish trust event if high risk
        if result['is_high_risk']:
            trust_event = {
                'event_type': 'high_risk_seller',
                'seller_id': seller_data.seller_id,
                'score': result['behavior_score'],
                'risk_level': result['risk_level'],
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': {
                    'components': result['components'],
                    'product_count': len(seller_data.products),
                    'complaint_count': len(seller_data.complaints),
                    'service': 'seller-behavior-analyzer'
                }
            }
            
            producer.produce(
                topic=KAFKA_TOPIC_TRUST_EVENTS,
                key=seller_data.seller_id.encode('utf-8'),
                value=json.dumps(trust_event).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing seller: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def consume_seller_events():
    """Consume seller events from Kafka and analyze them."""
    consumer = Consumer({
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'earliest'
    })
    
    consumer.subscribe([KAFKA_TOPIC_SELLER_EVENTS])
    
    logger.info(f"Started consuming messages from {KAFKA_TOPIC_SELLER_EVENTS}")
    
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
                seller_data = json.loads(msg.value().decode('utf-8'))
                seller_id = seller_data.get('seller_id')
                logger.info(f"Processing seller: {seller_id}")
                
                # Analyze the seller
                result = analyzer.analyze_seller(seller_data)
                
                # Publish trust event if high risk
                if result['is_high_risk']:
                    trust_event = {
                        'event_type': 'high_risk_seller',
                        'seller_id': seller_id,
                        'score': result['behavior_score'],
                        'risk_level': result['risk_level'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'metadata': {
                            'components': result['components'],
                            'product_count': len(seller_data.get('products', [])),
                            'complaint_count': len(seller_data.get('complaints', [])),
                            'service': 'seller-behavior-analyzer'
                        }
                    }
                    
                    producer.produce(
                        topic=KAFKA_TOPIC_TRUST_EVENTS,
                        key=seller_id.encode('utf-8'),
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
    consumer_thread = threading.Thread(target=asyncio.run, args=(consume_seller_events(),))
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Start the FastAPI server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        log_level="info",
        reload=True
    )
