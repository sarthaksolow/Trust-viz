# services/swarm-intelligence/main.py
# Run with:
# uvicorn main:app --host 0.0.0.0 --port 5001 --reload

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import os, json, random, logging

from crewai import Agent, Crew, Task
from crewai.llm import LLM

# ------------------------------
# Logging
# ------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SwarmIntelligence")

# ------------------------------
# FastAPI setup
# ------------------------------
app = FastAPI(title="Swarm Intelligence")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ------------------------------
# Memory files
# ------------------------------
PATTERN_MEMORY_FILE = "pattern_memory.json"
LEARNED_PATTERNS_FILE = "learned_patterns.json"
TRUST_EVENTS_FILE = "trust_events.json"

def load_memory(file: str) -> List[dict]:
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_memory(file: str, data: List[dict]):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ------------------------------
# CrewAI Setup
# ------------------------------
llm = LLM(model="groq/llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

price_agent = Agent(
    role="Price Analyst",
    goal="Detect abnormal pricing patterns",
    backstory="Evaluates if product prices deviate from benchmarks or history.",
    llm=llm,
)

review_agent = Agent(
    role="Review Inspector",
    goal="Detect fake or spammy reviews",
    backstory="Looks at review sentiment, duplication, and suspicious wording.",
    llm=llm,
)

seller_agent = Agent(
    role="Seller Monitor",
    goal="Assess seller behavior and trustworthiness",
    backstory="Checks account history, return ratios, and sudden changes.",
    llm=llm,
)

consensus_agent = Agent(
    role="Consensus Judge",
    goal="Combine findings into a final trust score",
    backstory="Aggregates swarm agent signals into one decision.",
    llm=llm,
)

# ------------------------------
# Pydantic models
# ------------------------------
class AnalysisRequest(BaseModel):
    data: Dict[str, Any]

# ------------------------------
# Core swarm analysis
# ------------------------------
def run_swarm_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    # 20% chance exploration → store new signal field
    if random.random() < 0.2:
        mem = load_memory(PATTERN_MEMORY_FILE)
        explore_field = random.choice(list(data.keys()))
        mem.append({"product_id": data.get("product_id"), "explore_field": explore_field})
        save_memory(PATTERN_MEMORY_FILE, mem)

    # Define consensus task
    task = Task(
        description=f"""
        Analyze this product listing data and output structured JSON.
        Data: {json.dumps(data)}

        Return JSON with fields:
        - fraud_signals: list of strings
        - trust_score: float (0-1)
        - confidence: float (0-1)
        - explanation: string
        """,
        agent=consensus_agent,
        expected_output="JSON with fraud_signals, trust_score, confidence, explanation",
    )

    crew = Crew(agents=[price_agent, review_agent, seller_agent, consensus_agent], tasks=[task])
    result = crew.kickoff()

    # ✅ unwrap CrewOutput
    raw_output = result.raw if hasattr(result, "raw") else str(result)

    try:
        result_json = json.loads(raw_output)
    except Exception:
        result_json = {
            "fraud_signals": ["ParseError"],
            "trust_score": 0.5,
            "confidence": 0.5,
            "explanation": raw_output
        }

    return {
        "product_id": data.get("product_id"),
        "fraud_score": result_json.get("trust_score", 0),
        "details": {
            "trust_score": result_json.get("trust_score", 0),
            "confidence": result_json.get("confidence", 0),
            "fraud_signals": result_json.get("fraud_signals", []),
            "explanation": result_json.get("explanation", ""),
        }
    }

# ------------------------------
# Endpoints
# ------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Swarm Intelligence", "agents": 4}

@app.post("/analyze")
def analyze(request: AnalysisRequest):
    try:
        return run_swarm_analysis(request.data)
    except Exception as e:
        logger.error(f"❌ Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def simulate():
    """Run analysis on 10 synthetic products."""
    products = [
        {"product_id": f"prod_{i}", "seller_id": f"seller_{i}", "price": random.randint(10, 200),
         "quantity": random.randint(1, 50), "recent_reviews": ["Great!", "Bad", "Looks fake"],
         "seller_history": {"account_age_days": random.randint(10, 400), "total_sales": random.randint(1, 500)}}
        for i in range(10)
    ]
    results = [run_swarm_analysis(p) for p in products]

    # Save trust events
    trust_events = load_memory(TRUST_EVENTS_FILE)
    for r in results:
        trust_events.append({
            "product_id": r["product_id"],
            "trust_score": r["details"]["trust_score"],
            "confidence": r["details"]["confidence"],
            "fraud_signals": r["details"]["fraud_signals"],
        })
    save_memory(TRUST_EVENTS_FILE, trust_events)
    return results

@app.get("/trust_events")
def get_trust_events():
    return {"trust_events": load_memory(TRUST_EVENTS_FILE)}

@app.delete("/trust_events")
def clear_trust_events():
    save_memory(TRUST_EVENTS_FILE, [])
    return {"message": "Trust events cleared"}

