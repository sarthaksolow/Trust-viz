# To run the server, use:
# uvicorn main:app --host 0.0.0.0 --port 5001 --reload

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
import json
import os
import logging
from crew import FraudDetectionCrew
from dotenv import load_dotenv
from reinforcement_learner import ReinforcementLearner
import asyncio
import threading

load_dotenv()

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
# Global Variables (replacing Kafka for now)
# ----------------------------------
reinforcement_learner = None
simulation_running = False

# Mock Kafka functionality with in-memory queues
raw_data_queue = []
trust_events_queue = []

# ----------------------------------
# FastAPI Startup & Shutdown
# ----------------------------------
@app.on_event("startup")
def startup_event():
    global reinforcement_learner
    logger.info("🚀 Starting Swarm Intelligence Service...")
    
    try:
        reinforcement_learner = ReinforcementLearner()
        logger.info("✅ ReinforcementLearner initialized.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize ReinforcementLearner: {e}")
        # Allow service to start without RL if it fails

@app.on_event("shutdown")
def shutdown_event():
    logger.info("🧼 Swarm Intelligence Service shutting down.")

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

class ProductData(BaseModel):
    product_id: str
    seller_id: str
    product_name: str
    price: float
    product_image_url: str = ""
    quantity: int = 0
    historical_prices: List[float] = []
    market_benchmarks: Dict[str, float] = {}
    recent_reviews: List[str] = []
    reviewer_trust_scores: Dict[str, float] = {}
    seller_history: Dict[str, Any] = {}
    listing_patterns: Dict[str, Any] = {}
    return_refund_ratios: float = 0.0
    complaint_history: List[Dict] = []
    perceptual_ai_score: float = 0.0

# ----------------------------------
# Helper Functions
# ----------------------------------
def process_fraud_detection(product_data: dict) -> dict:
    """Process fraud detection using CrewAI"""
    try:
        dynamic_prompts = {}
        if reinforcement_learner:
            reinforcement_learner.learn_from_patterns()
            dynamic_prompts = reinforcement_learner.get_dynamic_prompts()
            logger.info(f"Fetched dynamic prompts: {dynamic_prompts}")

        fraud_crew = FraudDetectionCrew(product_data, dynamic_prompts)
        crew_result_str = fraud_crew.run()
        logger.info(f"CrewAI Result: {crew_result_str}")

        # Parse the structured JSON output
        try:
            crew_output = json.loads(crew_result_str)
            return {
                "trust_score": crew_output.get('final_trust_score', 0.5),
                "fraud_signals": crew_output.get('fraud_signals', []),
                "confidence": crew_output.get('confidence', 0.0),
                "explanation": crew_output.get('explanation', 'CrewAI analysis completed.')
            }
        except json.JSONDecodeError as parse_e:
            logger.error(f"Failed to parse CrewAI result as JSON: {parse_e}")
            return {
                "trust_score": 0.0,
                "fraud_signals": ["json_parse_error"],
                "confidence": 0.0,
                "explanation": f"CrewAI output parsing failed: {str(parse_e)}"
            }
    except Exception as e:
        logger.error(f"Error running CrewAI: {e}")
        return {
            "trust_score": 0.0,
            "fraud_signals": ["crew_execution_failed"],
            "confidence": 0.0,
            "explanation": f"CrewAI execution failed: {str(e)}"
        }

# ----------------------------------
# Endpoints
# ----------------------------------
@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    try:
        data = request.data
        logger.info(f"🧪 Manual analysis triggered: {data}")

        # Convert to ProductData format
        product_data = {
            "product_id": data.get("product_id", "unknown"),
            "seller_id": data.get("seller_id", "unknown"),
            "product_name": data.get("product_name", "Unknown Product"),
            "price": float(data.get("price", 0.0)),
            "product_image_url": data.get("product_image_url", ""),
            "quantity": int(data.get("quantity", 0)),
            "historical_prices": data.get("historical_prices", []),
            "market_benchmarks": data.get("market_benchmarks", {}),
            "recent_reviews": data.get("recent_reviews", []),
            "reviewer_trust_scores": data.get("reviewer_trust_scores", {}),
            "seller_history": data.get("seller_history", {}),
            "listing_patterns": data.get("listing_patterns", {}),
            "return_refund_ratios": float(data.get("return_refund_ratios", 0.0)),
            "complaint_history": data.get("complaint_history", []),
            "perceptual_ai_score": float(data.get("perceptual_ai_score", 0.0))
        }

        result = process_fraud_detection(product_data)
        return {
            "fraud_score": 1.0 - result["trust_score"],  # Convert trust to fraud score
            "agent_id": "crew-001",
            "details": result
        }
    except Exception as e:
        logger.error(f"❌ Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate", response_model=List[SimulationResult])
async def simulate_fraud_detection():
    """
    Runs the CrewAI swarm on 10 hardcoded synthetic product listings
    to demonstrate its behavior without needing live Kafka ingestion.
    """
    global simulation_running
    
    if simulation_running:
        raise HTTPException(status_code=409, detail="Simulation already running")
    
    simulation_running = True
    
    try:
        synthetic_listings = [
            {  # Clean listing
                "product_id": "sim_prod_001", "seller_id": "sim_seller_001", "product_name": "Genuine Leather Wallet",
                "price": 45.00, "product_image_url": "http://example.com/img/wallet_clean.jpg", "quantity": 100,
                "historical_prices": [45.00, 46.00, 44.50], "market_benchmarks": {"Leather Wallet": 50.00},
                "recent_reviews": ["High quality!", "Exactly as described."], "reviewer_trust_scores": {"userA": 0.95, "userB": 0.92},
                "seller_history": {"account_age_days": 500, "total_sales": 200, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.01, "complaint_history": [], "perceptual_ai_score": 0.98
            },
            {  # Suspicious Price
                "product_id": "sim_prod_002", "seller_id": "sim_seller_002", "product_name": "Luxury Smartwatch",
                "price": 50.00, "product_image_url": "http://example.com/img/watch_cheap.jpg", "quantity": 10,
                "historical_prices": [500.00, 510.00, 495.00], "market_benchmarks": {"Luxury Smartwatch": 550.00},
                "recent_reviews": ["Amazing deal!", "Unbelievable price."], "reviewer_trust_scores": {"userC": 0.7, "userD": 0.6},
                "seller_history": {"account_age_days": 50, "total_sales": 5, "category_changes": 1},
                "listing_patterns": {}, "return_refund_ratios": 0.1, "complaint_history": [], "perceptual_ai_score": 0.8
            },
            {  # Suspicious Reviews (burst)
                "product_id": "sim_prod_003", "seller_id": "sim_seller_003", "product_name": "Organic Coffee Beans",
                "price": 25.00, "product_image_url": "http://example.com/img/coffee.jpg", "quantity": 200,
                "historical_prices": [25.00, 25.00, 25.00], "market_benchmarks": {"Coffee Beans": 28.00},
                "recent_reviews": ["Best coffee ever!", "Five stars!", "Highly recommend!", "So fresh!"],
                "reviewer_trust_scores": {"userE": 0.5, "userF": 0.4, "userG": 0.55, "userH": 0.48},
                "seller_history": {"account_age_days": 120, "total_sales": 50, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.02, "complaint_history": [], "perceptual_ai_score": 0.95
            },
            {  # Suspicious Seller Behavior
                "product_id": "sim_prod_004", "seller_id": "sim_seller_004", "product_name": "Vintage Camera",
                "price": 180.00, "product_image_url": "http://example.com/img/camera.jpg", "quantity": 5,
                "historical_prices": [180.00], "market_benchmarks": {"Vintage Camera": 250.00},
                "recent_reviews": ["Looks good."], "reviewer_trust_scores": {"userI": 0.8},
                "seller_history": {"account_age_days": 10, "total_sales": 2, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.4, "complaint_history": [{"type": "high"}],
                "perceptual_ai_score": 0.9
            },
            {  # Suspicious Image
                "product_id": "sim_prod_005", "seller_id": "sim_seller_001", "product_name": "Designer Handbag",
                "price": 300.00, "product_image_url": "http://example.com/img/handbag_low_res.jpg", "quantity": 20,
                "historical_prices": [300.00, 310.00], "market_benchmarks": {"Designer Handbag": 350.00},
                "recent_reviews": ["Nice bag."], "reviewer_trust_scores": {"userJ": 0.85},
                "seller_history": {"account_age_days": 500, "total_sales": 150, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.03, "complaint_history": [], "perceptual_ai_score": 0.3
            },
            {  # Anomaly
                "product_id": "sim_prod_006", "seller_id": "sim_seller_005", "product_name": "Rare Collectible Coin",
                "price": 1200.00, "product_image_url": "http://example.com/img/coin.jpg", "quantity": 1,
                "historical_prices": [1200.00], "market_benchmarks": {"Collectible Coin": 1500.00},
                "recent_reviews": [], "reviewer_trust_scores": {},
                "seller_history": {"account_age_days": 90, "total_sales": 1, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.99
            },
            {  # Mixed signals
                "product_id": "sim_prod_007", "seller_id": "sim_seller_006", "product_name": "Gaming Console",
                "price": 150.00, "product_image_url": "http://example.com/img/console.jpg", "quantity": 30,
                "historical_prices": [400.00, 420.00], "market_benchmarks": {"Gaming Console": 450.00},
                "recent_reviews": ["Scam!", "Fake product."], "reviewer_trust_scores": {"userK": 0.2, "userL": 0.3},
                "seller_history": {"account_age_days": 180, "total_sales": 30, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.05, "complaint_history": [], "perceptual_ai_score": 0.7
            },
            {  # Clean listing 2
                "product_id": "sim_prod_008", "seller_id": "sim_seller_001", "product_name": "Ergonomic Office Chair",
                "price": 250.00, "product_image_url": "http://example.com/img/chair.jpg", "quantity": 50,
                "historical_prices": [250.00, 245.00, 255.00], "market_benchmarks": {"Office Chair": 260.00},
                "recent_reviews": ["Very comfortable.", "Good value."], "reviewer_trust_scores": {"userM": 0.9, "userN": 0.88},
                "seller_history": {"account_age_days": 600, "total_sales": 300, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.005, "complaint_history": [], "perceptual_ai_score": 0.99
            },
            {  # Category switch
                "product_id": "sim_prod_009", "seller_id": "sim_seller_007", "product_name": "Handmade Jewelry",
                "price": 75.00, "product_image_url": "http://example.com/img/jewelry.jpg", "quantity": 15,
                "historical_prices": [75.00], "market_benchmarks": {"Handmade Jewelry": 80.00},
                "recent_reviews": ["Beautiful craftsmanship."], "reviewer_trust_scores": {"userO": 0.8},
                "seller_history": {"account_age_days": 200, "total_sales": 10, "category_changes": 1},
                "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.9
            },
            {  # Compression artifacts
                "product_id": "sim_prod_010", "seller_id": "sim_seller_008", "product_name": "Limited Edition Sneakers",
                "price": 180.00, "product_image_url": "http://example.com/img/sneakers_compressed.jpg", "quantity": 5,
                "historical_prices": [180.00], "market_benchmarks": {"Limited Edition Sneakers": 200.00},
                "recent_reviews": ["Authentic."], "reviewer_trust_scores": {"userP": 0.75},
                "seller_history": {"account_age_days": 60, "total_sales": 3, "category_changes": 0},
                "listing_patterns": {}, "return_refund_ratios": 0.0, "complaint_history": [], "perceptual_ai_score": 0.6
            }
        ]

        results = []
        for i, listing in enumerate(synthetic_listings):
            logger.info(f"Running simulation for listing {i+1}: {listing['product_id']}")
            
            try:
                result_data = process_fraud_detection(listing)
                results.append(SimulationResult(
                    product_id=listing["product_id"],
                    final_trust_score=result_data["trust_score"],
                    fraud_signals=result_data["fraud_signals"],
                    confidence=result_data["confidence"],
                    explanation=result_data["explanation"]
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
    finally:
        simulation_running = False

@app.post("/process_product")
async def process_product(product_data: ProductData):
    """Process a single product through the fraud detection pipeline"""
    try:
        product_dict = product_data.dict()
        result = process_fraud_detection(product_dict)
        
        # Add to trust events queue (mock Kafka)
        trust_event = {
            "product_id": product_data.product_id,
            "seller_id": product_data.seller_id,
            "trust_score": result["trust_score"],
            "fraud_signals": result["fraud_signals"],
            "confidence": result["confidence"],
            "explanation": result["explanation"],
            "stage": "crewai_analysis"
        }
        trust_events_queue.append(trust_event)
        
        return {
            "status": "success",
            "product_id": product_data.product_id,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score")
async def handle_score(data: ScoreRequest):
    try:
        logger.info(f"Received trust score for product: {data.product_id}")

        trust_event = {
            "product_id": data.product_id,
            "seller_id": data.seller_id,
            "trust_score": data.trust_score,
            "reason": data.reason,
            "stage": "final"
        }

        # Add to mock trust events queue
        trust_events_queue.append(trust_event)
        
        return {"status": "success", "message": "Trust score logged successfully"}
    except Exception as e:
        logger.error(f"Error in /score: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Swarm Intelligence",
        "reinforcement_learner": reinforcement_learner is not None,
        "queue_status": {
            "raw_data_queue": len(raw_data_queue),
            "trust_events_queue": len(trust_events_queue)
        }
    }

@app.get("/trust_events")
def get_trust_events():
    """Get all trust events from the queue"""
    return {"trust_events": trust_events_queue}

@app.delete("/trust_events")
def clear_trust_events():
    """Clear the trust events queue"""
    global trust_events_queue
    count = len(trust_events_queue)
    trust_events_queue = []
    return {"message": f"Cleared {count} trust events"}

# ----------------------------------
# Background Task Functions (mock Kafka polling)
# ----------------------------------
def background_processor():
    """Background task to process raw data queue"""
    while True:
        try:
            if raw_data_queue:
                raw_event = raw_data_queue.pop(0)
                logger.info(f"Processing raw event: {raw_event}")
                
                # Process with CrewAI
                result = process_fraud_detection(raw_event)
                
                # Add result to trust events
                trust_event = {
                    "product_id": raw_event.get("product_id"),
                    "seller_id": raw_event.get("seller_id"),
                    "trust_score": result["trust_score"],
                    "fraud_signals": result["fraud_signals"],
                    "confidence": result["confidence"],
                    "explanation": result["explanation"],
                    "stage": "background_processing"
                }
                trust_events_queue.append(trust_event)
            
            # Small delay to prevent busy waiting
            import time
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error in background processor: {e}")
            import time
            time.sleep(5)

# Start background processor in a separate thread
@app.on_event("startup")
def start_background_tasks():
    import threading
    background_thread = threading.Thread(target=background_processor, daemon=True)
    background_thread.start()
    logger.info("Background processor started")