# To run the server, use:
# uvicorn main:app --host 0.0.0.0 --port 5001 --reload

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict
from confluent_kafka import Producer, Consumer, KafkaException
from fastapi_utils.tasks import repeat_every
import json
import os
import logging
from .crew import FraudDetectionCrew # Import the CrewAI setup
from dotenv import load_dotenv
from .reinforcement_learner import ReinforcementLearner # Import the ReinforcementLearner

load_dotenv() # Load environment variables for GROQ_API_KEY

# ----------------------------------
# Logging setup
# ----------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmIntelligence")

# ----------------------------------
# FastAPI App
# ----------------------------------
app = FastAPI(title="Swarm Intelligence")

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
reinforcement_learner = None # Global instance for the learner

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
    
    global reinforcement_learner
    try:
        reinforcement_learner = ReinforcementLearner()
        logger.info("✅ ReinforcementLearner initialized.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ReinforcementLearner: {e}")
        # Do not raise, allow service to start without RL if it fails

@app.on_event("shutdown")
def shutdown_event():
    if producer:
        producer.flush()
        logger.info("🧼 Kafka Producer flushed.")
    if consumer:
        consumer.close()
        logger.info("🧼 Kafka Consumer closed.")

# ----------------------------------
# Models
# ----------------------------------
class AnalysisRequest(BaseModel):
    data: Dict[Any, Any]

class ScoreRequest(BaseModel):
    product_id: str
    seller_id: str
    trust_score: float
    reason: str

class SimulationResult(BaseModel):
    product_id: str
    final_trust_score: float
    fraud_signals: List[str]
    confidence: float
    explanation: str

# ----------------------------------
# Endpoints
# ----------------------------------
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

@app.post("/simulate", response_model=List[SimulationResult])
async def simulate_fraud_detection():
    """
    Runs the CrewAI swarm on 10 hardcoded synthetic product listings
    to demonstrate its behavior without needing live Kafka ingestion.
    """
    synthetic_listings = [
        { # Clean listing
            "product_id": "sim_prod_001", "seller_id": "sim_seller_001", "product_name": "Genuine Leather Wallet",
            "price": 45.00, "product_image_url": "http://example.com/img/wallet_clean.jpg", "quantity": 100,
            "historical_prices": [45.00, 46.00, 44.50], "market_benchmarks": {"Leather Wallet": 50.00},
            "recent_reviews": ["High quality!", "Exactly as described."], "reviewer_trust_scores": {"userA": 0.95, "userB": 0.92},
            "seller_history": {"account_age_days": 500, "total_sales": 200, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.01, "complaint_history": [], "perceptual_ai_score": 0.98
        },
        { # Suspicious Price
            "product_id": "sim_prod_002", "seller_id": "sim_seller_002", "product_name": "Luxury Smartwatch",
            "price": 50.00, "product_image_url": "http://example.com/img/watch_cheap.jpg", "quantity": 10,
            "historical_prices": [500.00, 510.00, 495.00], "market_benchmarks": {"Luxury Smartwatch": 550.00},
            "recent_reviews": ["Amazing deal!", "Unbelievable price."], "reviewer_trust_scores": {"userC": 0.7, "userD": 0.6},
            "seller_history": {"account_age_days": 50, "total_sales": 5, "category_changes": 1},
            "listing_patterns": {}, "return_refund_ratios": 0.1, "complaint_history": [], "perceptual_ai_score": 0.8
        },
        { # Suspicious Reviews (burst)
            "product_id": "sim_prod_003", "seller_id": "sim_seller_003", "product_name": "Organic Coffee Beans",
            "price": 25.00, "product_image_url": "http://example.com/img/coffee.jpg", "quantity": 200,
            "historical_prices": [25.00, 25.00, 25.00], "market_benchmarks": {"Coffee Beans": 28.00},
            "recent_reviews": ["Best coffee ever!", "Five stars!", "Highly recommend!", "So fresh!"], # Simulate burst
            "reviewer_trust_scores": {"userE": 0.5, "userF": 0.4, "userG": 0.55, "userH": 0.48},
            "seller_history": {"account_age_days": 120, "total_sales": 50, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.02, "complaint_history": [], "perceptual_ai_score": 0.95
        },
        { # Suspicious Seller Behavior (new account, high returns)
            "product_id": "sim_prod_004", "seller_id": "sim_seller_004", "product_name": "Vintage Camera",
            "price": 180.00, "product_image_url": "http://example.com/img/camera.jpg", "quantity": 5,
            "historical_prices": [180.00], "market_benchmarks": {"Vintage Camera": 250.00},
            "recent_reviews": ["Looks good."], "reviewer_trust_scores": {"userI": 0.8},
            "seller_history": {"account_age_days": 10, "total_sales": 2, "category_changes": 0}, # New account
            "listing_patterns": {}, "return_refund_ratios": 0.4, "complaint_history": [{"type": "high"}], # High returns
            "perceptual_ai_score": 0.9
        },
        { # Suspicious Image (low perceptual score)
            "product_id": "sim_prod_005", "seller_id": "sim_seller_001", "product_name": "Designer Handbag",
            "price": 300.00, "product_image_url": "http://example.com/img/handbag_low_res.jpg", "quantity": 20,
            "historical_prices": [300.00, 310.00], "market_benchmarks": {"Designer Handbag": 350.00},
            "recent_reviews": ["Nice bag."], "reviewer_trust_scores": {"userJ": 0.85},
            "seller_history": {"account_age_days": 500, "total_sales": 150, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.03, "complaint_history": [], "perceptual_ai_score": 0.3 # Low image score
        },
        { # Anomaly (very low quantity for high price)
            "product_id": "sim_prod_006", "seller_id": "sim_seller_005", "product_name": "Rare Collectible Coin",
            "price": 1200.00, "product_image_url": "http://example.com/img/coin.jpg", "quantity": 1, # Low quantity
            "historical_prices": [1200.00], "market_benchmarks": {"Collectible Coin": 1500.00},
            "recent_reviews": [], "reviewer_trust_scores": {},
            "seller_history": {"account_age_days": 90, "total_sales": 1, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.99
        },
        { # Mixed signals (price and reviews)
            "product_id": "sim_prod_007", "seller_id": "sim_seller_006", "product_name": "Gaming Console",
            "price": 150.00, "product_image_url": "http://example.com/img/console.jpg", "quantity": 30,
            "historical_prices": [400.00, 420.00], "market_benchmarks": {"Gaming Console": 450.00}, # Low price
            "recent_reviews": ["Scam!", "Fake product."], "reviewer_trust_scores": {"userK": 0.2, "userL": 0.3}, # Bad reviews
            "seller_history": {"account_age_days": 180, "total_sales": 30, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.05, "complaint_history": [], "perceptual_ai_score": 0.7
        },
        { # Another clean listing
            "product_id": "sim_prod_008", "seller_id": "sim_seller_001", "product_name": "Ergonomic Office Chair",
            "price": 250.00, "product_image_url": "http://example.com/img/chair.jpg", "quantity": 50,
            "historical_prices": [250.00, 245.00, 255.00], "market_benchmarks": {"Office Chair": 260.00},
            "recent_reviews": ["Very comfortable.", "Good value."], "reviewer_trust_scores": {"userM": 0.9, "userN": 0.88},
            "seller_history": {"account_age_days": 600, "total_sales": 300, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.005, "complaint_history": [], "perceptual_ai_score": 0.99
        },
        { # Seller with sudden category switch (exploratory signal)
            "product_id": "sim_prod_009", "seller_id": "sim_seller_007", "product_name": "Handmade Jewelry",
            "price": 75.00, "product_image_url": "http://example.com/img/jewelry.jpg", "quantity": 15,
            "historical_prices": [75.00], "market_benchmarks": {"Handmade Jewelry": 80.00},
            "recent_reviews": ["Beautiful craftsmanship."], "reviewer_trust_scores": {"userO": 0.8},
            "seller_history": {"account_age_days": 200, "total_sales": 10, "category_changes": 1}, # Sudden switch
            "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.9
        },
        { # Product with high compression artifacts (exploratory signal)
            "product_id": "sim_prod_010", "seller_id": "sim_seller_008", "product_name": "Limited Edition Sneakers",
            "price": 180.00, "product_image_url": "http://example.com/img/sneakers_compressed.jpg", "quantity": 5,
            "historical_prices": [180.00], "market_benchmarks": {"Limited Edition Sneakers": 200.00},
            "recent_reviews": ["Authentic."], "reviewer_trust_scores": {"userP": 0.75},
            "seller_history": {"account_age_days": 60, "total_sales": 3, "category_changes": 0},
            "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.6 # Lower score for artifacts
        }
    ]

    results = []
    for i, listing in enumerate(synthetic_listings):
        logger.info(f"Running simulation for listing {i+1}: {listing['product_id']}")
        
        dynamic_prompts = {}
        if reinforcement_learner:
            # In a simulation, we might not want to trigger learning on every run,
            # but we still want to use any learned patterns.
            # reinforcement_learner.learn_from_patterns() # Don't learn during simulation
            dynamic_prompts = reinforcement_learner.get_dynamic_prompts()

        product_data_for_crew = {
            "product_id": listing.get("product_id"),
            "seller_id": listing.get("seller_id"),
            "product_name": listing.get("product_name"),
            "price": listing.get("price"),
            "product_image_url": listing.get("product_image_url"),
            "quantity": listing.get("quantity", 0),
            "historical_prices": listing.get("historical_prices", []),
            "market_benchmarks": listing.get("market_benchmarks", {}),
            "recent_reviews": listing.get("recent_reviews", []),
            "reviewer_trust_scores": listing.get("reviewer_trust_scores", {}),
            "seller_history": listing.get("seller_history", {}),
            "listing_patterns": listing.get("listing_patterns", {}),
            "return_refund_ratios": listing.get("return_refund_ratios", 0.0),
            "complaint_history": listing.get("complaint_history", []),
            "perceptual_ai_score": listing.get("perceptual_ai_score", 0.0)
        }

        try:
            fraud_crew = FraudDetectionCrew(product_data_for_crew, dynamic_prompts)
            crew_result_str = fraud_crew.run()
            
            crew_output = json.loads(crew_result_str)
            results.append(SimulationResult(
                product_id=listing["product_id"],
                final_trust_score=crew_output.get('final_trust_score', 0.5),
                fraud_signals=crew_output.get('fraud_signals', []),
                confidence=crew_output.get('confidence', 0.0),
                explanation=crew_output.get('explanation', 'Simulation analysis completed.')
            ))
        except Exception as e:
            logger.error(f"Error during simulation for {listing['product_id']}: {e}")
            results.append(SimulationResult(
                product_id=listing["product_id"],
                final_trust_score=0.0,
                fraud_signals=["simulation_failed"],
                confidence=0.0,
                explanation=f"Simulation failed: {e}"
            ))
    return results

@app.post("/score")
async def handle_score(data: ScoreRequest):
    try:
        logger.info(f"📊 Received trust score for product: {data.product_id}")

        trust_event = {
            "product_id": data.product_id,
            "seller_id": data.seller_id,
            "trust_score": data.trust_score,
            "reason": data.reason,
            "stage": "final"
        }

        producer.produce(
            KAFKA_TOPIC_TRUST_EVENTS,
            key=data.seller_id.encode('utf-8'),
            value=json.dumps(trust_event).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()

        return {"status": "success", "message": "Trust score sent to Trust Ledger"}
    except Exception as e:
        logger.error(f"❌ Error in /score: {e}")
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
    global consumer, reinforcement_learner
    try:
        msg = consumer.poll(1.0)
        if msg is None:
            return
        if msg.error():
            raise KafkaException(msg.error())

        raw_event = json.loads(msg.value().decode('utf-8'))
        logger.info(f"📥 Received raw event: {raw_event}")

        dynamic_prompts = {}
        if reinforcement_learner:
            # Periodically trigger learning (e.g., every N events or on a separate schedule)
            # For simplicity, we'll call it here, but a dedicated learning loop might be better.
            reinforcement_learner.learn_from_patterns()
            dynamic_prompts = reinforcement_learner.get_dynamic_prompts()
            logger.info(f"Fetched dynamic prompts: {dynamic_prompts}")

        # Prepare data for CrewAI, populating fields from raw_event as requested
        # Note: 'reviews' and 'seller_history' are not typically part of the initial 'raw-data' event
        # from the data-ingestion service. In a full system, these would be fetched from
        # the Review Analyzer and Seller Behavior Analyzer services/databases.
        product_data_for_crew = {
            "product_id": raw_event.get("product_id"),
            "seller_id": raw_event.get("seller_id"),
            "product_name": raw_event.get("product_name"),
            "price": raw_event.get("price"),
            "product_image_url": raw_event.get("product_image_url"),
            "quantity": raw_event.get("quantity", 0), # For AnomalyDetectionAgent
            # Placeholder/empty for data not in raw_event, but expected by agents
            "historical_prices": raw_event.get("historical_prices", []), # Assuming raw_event might contain this in future
            "market_benchmarks": raw_event.get("market_benchmarks", {}), # Assuming raw_event might contain this in future
            "recent_reviews": raw_event.get("reviews", []), # User requested 'reviews'
            "reviewer_trust_scores": raw_event.get("reviewer_trust_scores", {}),
            "seller_history": raw_event.get("seller_history", {}), # User requested 'seller_history'
            "listing_patterns": raw_event.get("listing_patterns", {}),
            "return_refund_ratios": raw_event.get("return_refund_ratios", 0.0),
            "complaint_history": raw_event.get("complaint_history", []),
            "perceptual_ai_score": raw_event.get("perceptual_ai_score", 0.0)
        }

        # Execute CrewAI for fraud detection
        try:
            fraud_crew = FraudDetectionCrew(product_data_for_crew, dynamic_prompts)
            crew_result_str = fraud_crew.run()
            logger.info(f"CrewAI Result: {crew_result_str}")

            # Parse the structured JSON output from the OrchestratorAgent
            try:
                crew_output = json.loads(crew_result_str)
                trust_score = crew_output.get('final_trust_score', 0.5)
                reason = crew_output.get('explanation', 'CrewAI analysis completed.')
                fraud_signals = crew_output.get('fraud_signals', [])
                confidence = crew_output.get('confidence', 0.0)
                logger.info(f"Parsed CrewAI Output: Score={trust_score}, Signals={fraud_signals}, Confidence={confidence}, Reason={reason}")
            except json.JSONDecodeError as parse_e:
                logger.error(f"Failed to parse CrewAI result as JSON: {parse_e}. Raw output: {crew_result_str}")
                trust_score = 0.0
                reason = f"CrewAI output parsing failed: {parse_e}. Raw output: {crew_result_str[:200]}..."
            except Exception as parse_e:
                logger.error(f"Unexpected error parsing CrewAI result: {parse_e}. Raw output: {crew_result_str}")
                trust_score = 0.0
                reason = f"CrewAI output parsing failed: {parse_e}. Raw output: {crew_result_str[:200]}..."

            # 1. Image check request (still needed for Perceptual AI)
            image_payload = {
                "product_id": raw_event["product_id"],
                "product_image_url": raw_event.get("product_image_url", "")
            }
            producer.produce(
                KAFKA_TOPIC_IMAGE_CHECK,
                key=raw_event["product_id"].encode('utf-8'),
                value=json.dumps(image_payload).encode('utf-8'),
                callback=delivery_report
            )

            # 2. Trust events (now based on CrewAI)
            trust_payload = {
                "seller_id": raw_event["seller_id"],
                "product_id": raw_event["product_id"],
                "trust_score": trust_score,
                "reason": reason,
                "stage": "crewai_analysis",
                "fraud_signals": fraud_signals, # Include signals from orchestrator
                "confidence": confidence # Include confidence from orchestrator
            }
            producer.produce(
                KAFKA_TOPIC_TRUST_EVENTS,
                key=raw_event["seller_id"].encode('utf-8'),
                value=json.dumps(trust_payload).encode('utf-8'),
                callback=delivery_report
            )

            producer.flush()

        except RuntimeError as crew_e:
            logger.error(f"🚨 Error running CrewAI: {crew_e}")
            # Fallback or send a default suspicious event if CrewAI fails
            trust_payload = {
                "seller_id": raw_event["seller_id"],
                "product_id": raw_event["product_id"],
                "trust_score": 0.0,
                "reason": f"CrewAI system failed: {crew_e}",
                "stage": "crewai_failure"
            }
            producer.produce(
                KAFKA_TOPIC_TRUST_EVENTS,
                key=raw_event["seller_id"].encode('utf-8'),
                value=json.dumps(trust_payload).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()

    except Exception as e:
        logger.error(f"🚨 Error during raw-data polling: {e}")
