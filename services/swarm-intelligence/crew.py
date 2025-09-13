import os
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import logging
import json
import random
from crewai_tools import tool # Import tool decorator
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib # For saving/loading the model

load_dotenv() # Load environment variables from .env file

logger = logging.getLogger(__name__)

# Define the path for the pattern memory JSON file
PATTERN_MEMORY_FILE = "services/swarm-intelligence/pattern_memory.json"
ISOLATION_FOREST_MODEL_PATH = "services/swarm-intelligence/isolation_forest_model.joblib"

# Ensure the pattern_memory.json file exists and is a valid JSON array
def initialize_pattern_memory_file():
    if not os.path.exists(PATTERN_MEMORY_FILE):
        with open(PATTERN_MEMORY_FILE, 'w') as f:
            json.dump([], f)
    else:
        # Validate if it's a valid JSON array, if not, reinitialize
        try:
            with open(PATTERN_MEMORY_FILE, 'r') as f:
                content = json.load(f)
                if not isinstance(content, list):
                    raise ValueError("Pattern memory file is not a JSON array.")
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Invalid {PATTERN_MEMORY_FILE} detected. Reinitializing.")
            with open(PATTERN_MEMORY_FILE, 'w') as f:
                json.dump([], f)

initialize_pattern_memory_file()

@tool("Log Pattern Memory")
def log_pattern_memory(signal_data: str) -> str:
    """
    Logs an exploratory fraud signal into a JSON file for future use.
    The input should be a JSON string containing the signal details.
    """
    try:
        signal = json.loads(signal_data)
        with open(PATTERN_MEMORY_FILE, 'r+') as f:
            file_content = json.load(f)
            file_content.append(signal)
            f.seek(0)
            json.dump(file_content, f, indent=4)
            f.truncate()
        logger.info(f"Logged exploratory signal: {signal}")
        return "Exploratory signal logged successfully."
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON input for log_pattern_memory: {signal_data}")
        return "Failed to log signal: Invalid JSON input."
    except Exception as e:
        logger.error(f"Error logging pattern memory: {e}")
        return f"Failed to log signal: {e}"

# Initialize Isolation Forest Model
def initialize_isolation_forest_model():
    if os.path.exists(ISOLATION_FOREST_MODEL_PATH):
        try:
            model = joblib.load(ISOLATION_FOREST_MODEL_PATH)
            logger.info("Isolation Forest model loaded successfully.")
            return model
        except Exception as e:
            logger.warning(f"Failed to load Isolation Forest model: {e}. Training a new one.")
    
    # If no model or failed to load, train a simple one
    # This is a placeholder for a real-world training pipeline
    rng = np.random.RandomState(42)
    X = 0.3 * rng.randn(100, 2)
    X_train = np.r_[X + 2, X - 2] # Normal data
    
    # Add some outliers
    X_outliers = rng.uniform(low=-6, high=6, size=(20, 2))
    X_train = np.r_[X_train, X_outliers]

    model = IsolationForest(random_state=rng, contamination=0.1)
    model.fit(X_train)
    joblib.dump(model, ISOLATION_FOREST_MODEL_PATH)
    logger.info("New Isolation Forest model trained and saved.")
    return model

isolation_forest_model = initialize_isolation_forest_model()

@tool("Run Isolation Forest")
def run_isolation_forest(structured_data_json: str) -> str:
    """
    Runs Isolation Forest on structured numerical data to detect anomalies.
    Input should be a JSON string representing a dictionary of numerical features.
    Returns a JSON string with 'anomaly_score' (float) and 'is_outlier' (bool).
    """
    try:
        data = json.loads(structured_data_json)
        # Convert dictionary to pandas DataFrame for IsolationForest
        # Ensure consistent feature order and handle missing values
        feature_names = ['price', 'quantity', 'return_refund_ratios', 'complaint_count'] # Example features
        
        # Create a DataFrame with a single row for the current data point
        # Fill missing features with a default (e.g., 0 or mean/median from training data)
        input_df = pd.DataFrame([data])
        
        # Align columns with expected feature names, filling missing with 0
        for col in feature_names:
            if col not in input_df.columns:
                input_df[col] = 0.0 # Or a more appropriate default/imputation
        
        input_df = input_df[feature_names] # Ensure order

        # Predict anomaly score (-1 for outlier, 1 for inlier)
        # decision_function gives the raw anomaly score
        anomaly_score = isolation_forest_model.decision_function(input_df)[0]
        is_outlier = isolation_forest_model.predict(input_df)[0] == -1
        
        result = {
            "anomaly_score": float(anomaly_score),
            "is_outlier": bool(is_outlier),
            "confidence": max(0.0, min(1.0, 1 - (anomaly_score / 0.5))) # Simple confidence mapping
        }
        logger.info(f"Isolation Forest result: {result}")
        return json.dumps(result)
    except Exception as e:
        logger.error(f"Error running Isolation Forest: {e}")
        return json.dumps({"error": str(e), "anomaly_score": 0.0, "is_outlier": False, "confidence": 0.0})

# Initialize Groq LLM
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")
    
    groq_model_name = os.getenv("GROQ_MODEL_NAME", "llama-3-8b-instruct") # Default to llama-3-8b-instruct
    
    groq_llm = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=groq_model_name)
    logger.info(f"Groq LLM initialized successfully with model: {groq_model_name}.")
except Exception as e:
    logger.error(f"Error initializing Groq LLM: {e}")
    groq_llm = None # Handle case where LLM fails to initialize

class FraudDetectionAgents:
    def __init__(self, dynamic_prompts: Dict[str, str] = None):
        if not groq_llm:
            raise RuntimeError("Groq LLM not initialized. Cannot create agents.")
        self.dynamic_prompts = dynamic_prompts if dynamic_prompts is not None else {}

    def _get_backstory(self, agent_type: str, default_backstory: str) -> str:
        """Combines default backstory with dynamic prompt additions."""
        return default_backstory + self.dynamic_prompts.get(agent_type, "")

    def price_agent(self):
        default_backstory = """You are an expert in e-commerce pricing analysis. Your role is to identify pricing strategies that might indicate fraudulent activity, such as unusually low prices for high-value items, rapid price fluctuations, or prices that deviate significantly from established market rates. You are meticulous and use statistical methods to flag anomalies."""
        return Agent(
            role='Price Anomaly Detector',
            goal='Analyze product pricing data for suspicious patterns, sudden changes, or inconsistencies compared to market benchmarks.',
            backstory=self._get_backstory("price_agent", default_backstory),
            verbose=True,
            allow_delegation=False,
            llm=groq_llm,
            tools=[log_pattern_memory]
        )

    def anomaly_detection_agent(self):
        default_backstory = """You are a statistical anomaly detection expert. Your role is to apply unsupervised learning techniques, specifically Isolation Forest, to structured numerical data from product listings and seller behavior. You identify data points that deviate significantly from the norm, flagging them as potential outliers indicative of fraud."""
        return Agent(
            role='Anomaly Detection Specialist',
            goal='Detect statistical anomalies in structured product and seller data using Isolation Forest.',
            backstory=self._get_backstory("anomaly_detection_agent", default_backstory),
            verbose=True,
            allow_delegation=False,
            llm=groq_llm,
            tools=[run_isolation_forest, log_pattern_memory] # Add Isolation Forest tool
        )

    def review_agent(self):
        default_backstory = """You are a seasoned NLP specialist focused on review authenticity. You detect subtle linguistic cues, sentiment shifts, and temporal patterns that suggest reviews are not genuine. You are adept at spotting bot-generated content, review farming, and other deceptive practices."""
        return Agent(
            role='Review Authenticity Analyst',
            goal='Evaluate product reviews for signs of manipulation, fake content, or coordinated efforts to inflate/deflate ratings.',
            backstory=self._get_backstory("review_agent", default_backstory),
            verbose=True,
            allow_delegation=False,
            llm=groq_llm,
            tools=[log_pattern_memory]
        )

    def seller_agent(self):
        default_backstory = """You are a behavioral economics expert specializing in seller fraud. You analyze seller history, including shipping times, return rates, complaint history, and listing patterns. Your goal is to build a comprehensive risk profile and flag behaviors indicative of a legitimate seller turning fraudulent or a banned seller attempting to re-enter the marketplace."""
        return Agent(
            role='Seller Behavior Profiler',
            goal='Assess seller historical data and current activities to identify high-risk behaviors, such as relisting patterns, sudden changes in product categories, or unusual transaction volumes.',
            backstory=self._get_backstory("seller_agent", default_backstory),
            verbose=True,
            allow_delegation=False,
            llm=groq_llm,
            tools=[log_pattern_memory]
        )

    def image_agent(self):
        default_backstory = """You are a computer vision forensic expert. You scrutinize product images for any signs of digital alteration, low quality, inconsistencies in branding, or duplication across different listings. You are skilled at identifying synthetic artifacts and ensuring images represent genuine products."""
        return Agent(
            role='Image Authenticity Inspector',
            goal='Verify the authenticity of product images, detecting counterfeits, stolen content, AI-generated fakes, or subtle manipulations.',
            backstory=self._get_backstory("image_agent", default_backstory),
            verbose=True,
            allow_delegation=False,
            llm=groq_llm,
            tools=[log_pattern_memory]
        )

    def orchestrator_agent(self):
        return Agent(
            role='Fraud Consensus Agent',
            goal='Consolidate the findings from Price, Review, Seller, and Image agents to produce a final, comprehensive fraud assessment.',
            backstory="""You are the central intelligence unit, responsible for synthesizing diverse fraud signals. You weigh the evidence from each specialized agent, identify conflicting information, and derive a conclusive trust score. Your final output must be a structured JSON object, detailing all identified signals, the overall confidence in the assessment, and a clear explanation of the decision.""",
            verbose=True,
            allow_delegation=True, # Can delegate back to other agents if needed for clarification
            llm=groq_llm
        )

class FraudDetectionTasks:
    def __init__(self):
        pass # Tasks will be defined dynamically based on input

    def analyze_price(self, agent: Agent, product_data: Dict):
        return Task(
            description=f"""Analyze the pricing data for product {product_data.get('product_id', 'N/A')}.
            Product Name: {product_data.get('product_name', 'N/A')}
            Current Price: {product_data.get('price', 'N/A')}
            Historical Prices: {product_data.get('historical_prices', 'N/A')}
            Market Benchmarks: {product_data.get('market_benchmarks', 'N/A')}
            
            Identify any anomalies, sudden drops, or suspicious pricing strategies.
            Provide a fraud score (0-1) and a brief explanation.
            
            Additionally, with a 20% chance, perform an exploratory heuristic. For example, check if the current price is an exact match to a price from 6 months ago, which could indicate a relisting attempt after a ban. If an exploratory signal is found, use the 'Log Pattern Memory' tool to log it as a JSON string, including 'product_id' and 'seller_id'.
            
            After completing your analysis, log your final output (fraud score and explanation) using the standard Python logging module (e.g., `logger.info(json.dumps({'agent': 'PriceAgent', 'output': your_json_output}))`) before returning it.
            """,
            agent=agent,
            expected_output="A JSON object with 'fraud_score' (float) and 'explanation' (str). If an exploratory signal was logged, mention it in the explanation."
        )

    def analyze_reviews(self, agent: Agent, product_data: Dict):
        return Task(
            description=f"""Analyze the reviews associated with product {product_data.get('product_id', 'N/A')} and seller {product_data.get('seller_id', 'N/A')}.
            Recent Reviews: {product_data.get('recent_reviews', 'N/A')}
            Reviewer Trust Scores: {product_data.get('reviewer_trust_scores', 'N/A')}
            
            Detect any signs of fake reviews, review manipulation, or suspicious review patterns.
            Provide a fraud score (0-1) and a brief explanation.

            Additionally, with a 20% chance, perform an exploratory heuristic. For example, check for burst review patterns (multiple reviews from different users for the same product within a very short timeframe). If an exploratory signal is found, use the 'Log Pattern Memory' tool to log it as a JSON string, including 'product_id' and 'seller_id'.
            
            After completing your analysis, log your final output (fraud score and explanation) using the standard Python logging module (e.g., `logger.info(json.dumps({'agent': 'ReviewAgent', 'output': your_json_output}))`) before returning it.
            """,
            agent=agent,
            expected_output="A JSON object with 'fraud_score' (float) and 'explanation' (str). If an exploratory signal was logged, mention it in the explanation."
        )

    def analyze_seller_behavior(self, agent: Agent, product_data: Dict):
        return Task(
            description=f"""Analyze the behavior of seller {product_data.get('seller_id', 'N/A')} for product {product_data.get('product_id', 'N/A')}.
            Seller History: {product_data.get('seller_history', 'N/A')}
            Listing Patterns: {product_data.get('listing_patterns', 'N/A')}
            Return/Refund Ratios: {product_data.get('return_refund_ratios', 'N/A')}
            Complaint History: {product_data.get('complaint_history', 'N/A')}
            
            Identify high-risk behaviors, relisting fraud, or abrupt changes in selling patterns.
            Provide a fraud score (0-1) and a brief explanation.

            Additionally, with a 20% chance, perform an exploratory heuristic. For example, check for sudden category switches by the seller (e.g., from electronics to luxury goods). If an exploratory signal is found, use the 'Log Pattern Memory' tool to log it as a JSON string, including 'product_id' and 'seller_id'.
            
            After completing your analysis, log your final output (fraud score and explanation) using the standard Python logging module (e.g., `logger.info(json.dumps({'agent': 'SellerAgent', 'output': your_json_output}))`) before returning it.
            """,
            agent=agent,
            expected_output="A JSON object with 'fraud_score' (float) and 'explanation' (str). If an exploratory signal was logged, mention it in the explanation."
        )

    def analyze_image(self, agent: Agent, product_data: Dict):
        return Task(
            description=f"""Analyze the product image for product {product_data.get('product_id', 'N/A')}.
            Image URL: {product_data.get('product_image_url', 'N/A')}
            Perceptual AI Score: {product_data.get('perceptual_ai_score', 'N/A')}
            
            Detect counterfeits, stolen content, AI-generated fakes, or subtle manipulations.
            Provide a fraud score (0-1) and a brief explanation.

            Additionally, with a 20% chance, perform an exploratory heuristic. For example, check if the image has unusually high compression artifacts for its resolution, which could indicate multiple re-encodings or manipulation. If an exploratory signal is found, use the 'Log Pattern Memory' tool to log it as a JSON string, including 'product_id' and 'seller_id'.
            
            After completing your analysis, log your final output (fraud score and explanation) using the standard Python logging module (e.g., `logger.info(json.dumps({'agent': 'ImageAgent', 'output': your_json_output}))`) before returning it.
            """,
            agent=agent,
            expected_output="A JSON object with 'fraud_score' (float) and 'explanation' (str). If an exploratory signal was logged, mention it in the explanation."
        )

    def analyze_anomalies(self, agent: Agent, product_data: Dict):
        # Extract relevant numerical fields for Isolation Forest
        structured_fields = {
            "price": product_data.get("price", 0.0),
            "quantity": product_data.get("quantity", 0),
            "return_refund_ratios": product_data.get("return_refund_ratios", 0.0),
            "complaint_count": len(product_data.get("complaint_history", []))
        }
        return Task(
            description=f"""Analyze the structured numerical data for product {product_data.get('product_id', 'N/A')} using the 'Run Isolation Forest' tool.
            Structured Data: {json.dumps(structured_fields)}
            
            If an outlier is detected, produce an anomaly signal with a confidence score.
            Provide a fraud score (0-1) and a brief explanation, including whether an anomaly was detected and its confidence.
            
            After completing your analysis, log your final output (fraud score, explanation, anomaly_detected, anomaly_confidence) using the standard Python logging module (e.g., `logger.info(json.dumps({'agent': 'AnomalyDetectionAgent', 'output': your_json_output}))`) before returning it.
            """,
            agent=agent,
            expected_output="A JSON object with 'fraud_score' (float), 'explanation' (str), 'anomaly_detected' (bool), and 'anomaly_confidence' (float)."
        )

    def consolidate_fraud_assessment(self, agent: Agent, price_analysis: str, review_analysis: str, seller_analysis: str, image_analysis: str, anomaly_analysis: str):
        return Task(
            description=f"""Consolidate the following fraud analyses into a final assessment:
            Price Analysis: {price_analysis}
            Review Analysis: {review_analysis}
            Seller Behavior Analysis: {seller_analysis}
            Image Authenticity Analysis: {image_analysis}
            Anomaly Detection Analysis: {anomaly_analysis}
>>>>>>> Stashed changes

            Based on these inputs, determine an overall trust score (0-1, where 0 is high fraud risk, 1 is no fraud risk),
            list all significant fraud signals identified, provide a confidence level for your assessment (0-1),
            and give a comprehensive explanation for the final decision. This explanation MUST synthesize and explicitly reference the key findings and explanations from each individual agent (Price, Review, Seller, Image, Anomaly).

            Your final output MUST be a structured JSON object with the following keys:
            'final_trust_score': float (0-1)
            'fraud_signals': list of strings
            'confidence': float (0-1)
            'explanation': string
            """,
            agent=agent,
            expected_output="A JSON object with 'final_trust_score' (float), 'fraud_signals' (list of strings), 'confidence' (float), and 'explanation' (string) that includes summaries from all agents."
        )

class FraudDetectionCrew:
    def __init__(self, product_data: Dict, dynamic_prompts: Dict[str, str] = None):
        self.agents = FraudDetectionAgents(dynamic_prompts)
        self.tasks = FraudDetectionTasks()
        self.product_data = product_data

    def run(self):
        price_agent = self.agents.price_agent()
        review_agent = self.agents.review_agent()
        seller_agent = self.agents.seller_agent()
        image_agent = self.agents.image_agent()
        anomaly_agent = self.agents.anomaly_detection_agent() # New agent
        orchestrator_agent = self.agents.orchestrator_agent()

        price_task = self.tasks.analyze_price(price_agent, self.product_data)
        review_task = self.tasks.analyze_reviews(review_agent, self.product_data)
        seller_task = self.tasks.analyze_seller_behavior(seller_agent, self.product_data)
        image_task = self.tasks.analyze_image(image_agent, self.product_data)
        anomaly_task = self.tasks.analyze_anomalies(anomaly_agent, self.product_data) # New task

        # The orchestrator task depends on the output of all other tasks
        orchestrator_task = self.tasks.consolidate_fraud_assessment(
            orchestrator_agent,
            price_analysis=price_task,
            review_analysis=review_task,
            seller_analysis=seller_task,
            image_analysis=image_task,
            anomaly_analysis=anomaly_task # Include new anomaly task
        )

        crew = Crew(
            agents=[price_agent, review_agent, seller_agent, image_agent, anomaly_agent, orchestrator_agent],
            tasks=[price_task, review_task, seller_task, image_task, anomaly_task, orchestrator_task],
            process=Process.hierarchical,
            verbose=True
        )

        result = crew.kickoff()
        return result

if __name__ == "__main__":
    # Example usage
    example_product_data = {
        "product_id": "prod123",
        "seller_id": "seller456",
        "product_name": "Luxury Watch",
        "price": 150.00,
        "product_image_url": "http://example.com/image.jpg",
        "historical_prices": [150.00, 160.00, 155.00],
        "market_benchmarks": {"Luxury Watch": 200.00},
        "recent_reviews": ["Great product!", "Fast shipping."],
        "reviewer_trust_scores": {"user1": 0.9, "user2": 0.7},
        "seller_history": {"account_age_days": 300, "total_sales": 100},
        "listing_patterns": {"category_changes": 0},
        "return_refund_ratios": 0.05,
        "complaint_history": [],
        "perceptual_ai_score": 0.85,
        "quantity": 50, # Added for anomaly detection
        "complaint_history": [{"type": "low"}, {"type": "medium"}] # Added for anomaly detection
    }
    
    try:
        fraud_crew = FraudDetectionCrew(example_product_data)
        crew_result = fraud_crew.run()
        print("\n\nCrewAI Fraud Detection Result:")
        print(crew_result)
    except RuntimeError as e:
        print(f"Error running fraud detection crew: {e}")
