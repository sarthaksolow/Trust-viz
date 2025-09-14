import json
import os
import logging
from typing import Dict, List, Any
import faiss
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

PATTERN_MEMORY_FILE = "services/swarm-intelligence/pattern_memory.json"
# Placeholder for confirmed fraud outcomes from Trust Ledger
# In a real scenario, this would involve querying a persistent Trust Ledger database.
CONFIRMED_FRAUD_OUTCOMES = [
    {"product_id": "prod_fraud_1", "seller_id": "seller_fraud_1", "is_fraud": True, "fraud_type": "price_manipulation"},
    {"product_id": "prod_fraud_2", "seller_id": "seller_fraud_2", "is_fraud": True, "fraud_type": "fake_reviews"},
    {"product_id": "prod_clean_1", "seller_id": "seller_clean_1", "is_fraud": False},
]

class ReinforcementLearner:
    def __init__(self, embedding_dimension: int = 128):
        self.embedding_dimension = embedding_dimension
        self.index = faiss.IndexFlatL2(self.embedding_dimension) # L2 distance for similarity
        self.learned_patterns = [] # Keep a list of patterns for now
        self.pattern_embeddings = [] # Store embeddings alongside patterns
        self._load_learned_patterns() # Load from disk if available
        logger.info(f"ReinforcementLearner initialized. Loaded {len(self.learned_patterns)} learned patterns.")

    def _pattern_to_embedding(self, pattern: Dict) -> np.ndarray:
        """Converts a pattern dictionary to a numerical embedding (placeholder)."""
        # In a real system, this would use a more sophisticated embedding model
        # (e.g., sentence transformers, or even train a custom one).
        # For now, create a simple embedding based on hashing the JSON string.
        pattern_string = json.dumps(pattern, sort_keys=True)
        hash_value = hash(pattern_string) % (10**8) # Limit size
        embedding = np.random.rand(self.embedding_dimension).astype('float32') # Placeholder
        embedding[0] = hash_value # Inject some information
        return embedding

    def _load_learned_patterns(self):
        """Loads learned patterns and their embeddings from persistent storage."""
        learned_patterns_path = "services/swarm-intelligence/learned_patterns.json"
        if os.path.exists(learned_patterns_path):
            try:
                with open(learned_patterns_path, 'r') as f:
                    self.learned_patterns = json.load(f)
                    self.pattern_embeddings = [self._pattern_to_embedding(p) for p in self.learned_patterns]
                    self.pattern_embeddings = np.array(self.pattern_embeddings).astype('float32')
                    self.index = faiss.IndexFlatL2(self.embedding_dimension) # Re-initialize index
                    self.index.add(self.pattern_embeddings) # Add embeddings to index
                    logger.info(f"Loaded {len(self.learned_patterns)} learned patterns and embeddings.")
            except json.JSONDecodeError:
                logger.warning(f"Invalid {learned_patterns_path} detected. Starting with empty patterns.")
                self.learned_patterns = []
                self.pattern_embeddings = []
                self.index = faiss.IndexFlatL2(self.embedding_dimension)
        else:
            self.learned_patterns = []
            self.pattern_embeddings = []
            self.index = faiss.IndexFlatL2(self.embedding_dimension)

    def _save_learned_patterns(self):
        """Saves learned patterns and their embeddings to persistent storage."""
        learned_patterns_path = "services/swarm-intelligence/learned_patterns.json"
        with open(learned_patterns_path, 'w') as f:
            json.dump(self.learned_patterns, f, indent=4)
        # No need to save embeddings separately with faiss

    def _read_exploratory_signals(self) -> List[Dict]:
        """Reads all exploratory signals from pattern_memory.json."""
        if not os.path.exists(PATTERN_MEMORY_FILE):
            return []
        try:
            with open(PATTERN_MEMORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding {PATTERN_MEMORY_FILE}. It might be corrupted.")
            return []

    def _get_confirmed_fraud_outcomes(self, product_id: str = None, seller_id: str = None) -> List[Dict]:
        """
        Simulates fetching confirmed fraud outcomes from the Trust Ledger.
        In a real system, this would query a persistent Trust Ledger.
        """
        if product_id:
            return [o for o in CONFIRMED_FRAUD_OUTCOMES if o.get("product_id") == product_id]
        if seller_id:
            return [o for o in CONFIRMED_FRAUD_OUTCOMES if o.get("seller_id") == seller_id]
        return CONFIRMED_FRAUD_OUTCOMES

    def learn_from_patterns(self):
        """
        Reads exploratory signals and confirmed fraud outcomes,
        rewards useful patterns, and updates learned patterns.
        """
        exploratory_signals = self._read_exploratory_signals()
        logger.info(f"Read {len(exploratory_signals)} exploratory signals.")

        new_useful_patterns = []

        for signal in exploratory_signals:
            signal_type = signal.get("type")
            product_id = signal.get("product_id")
            seller_id = signal.get("seller_id")
            heuristic = signal.get("heuristic")
            
            # Check if this signal correlates with a confirmed fraud outcome
            # This is a simplified correlation. A real RL would be more sophisticated.
            confirmed_outcomes = self._get_confirmed_fraud_outcomes(product_id=product_id, seller_id=seller_id)
            
            is_useful = False
            for outcome in confirmed_outcomes:
                if outcome.get("is_fraud") and outcome.get("fraud_type") == signal_type:
                    is_useful = True
                    break
            
            if is_useful:
                # Reward this pattern
                pattern = {
                    "type": signal_type,
                    "heuristic": heuristic,
                    "reward_score": signal.get("reward_score", 0) + 1, # Increment reward
                    "last_rewarded": str(datetime.now()),
                    "decay_factor": 0.9 # Example decay factor
                }
                new_useful_patterns.append(pattern)
                logger.info(f"Rewarded useful pattern: {pattern}")
            else:
                # Explore more signals: add some new signals even if not immediately useful
                if random.random() < 0.1: # 10% chance of adding a new signal
                    new_heuristic = f"variation_of_{heuristic}" # Example
                    pattern = {
                        "type": signal_type,
                        "heuristic": new_heuristic,
                        "reward_score": 0.1, # Initial small reward
                        "last_rewarded": str(datetime.now()),
                        "decay_factor": 0.9
                    }
                    new_useful_patterns.append(pattern)
                    logger.info(f"Exploring new signal: {pattern}")

        # Update self.learned_patterns (using vector database)
        logger.info(f"Adding {len(new_useful_patterns)} new patterns to learned patterns.")
        for new_pattern in new_useful_patterns:
            embedding = self._pattern_to_embedding(new_pattern)
            self.pattern_embeddings.append(embedding)
            self.learned_patterns.append(new_pattern)
            self.index.add(np.array([embedding]).astype('float32')) # Add to faiss index

        # Decay rewards of existing patterns
        for i, pattern in enumerate(self.learned_patterns):
            if "decay_factor" in pattern and "last_rewarded" in pattern:
                try:
                    last_rewarded = datetime.fromisoformat(pattern["last_rewarded"])
                    time_since_reward = datetime.now() - last_rewarded
                    decay_amount = pattern["reward_score"] * pattern["decay_factor"] * (time_since_reward.days / 30) # Monthly decay
                    pattern["reward_score"] = max(0, pattern["reward_score"] - decay_amount)
                    self.learned_patterns[i] = pattern
                    logger.info(f"Decayed reward for pattern: {pattern}, Decay Amount: {decay_amount}")
                except Exception as e:
                    logger.warning(f"Error decaying reward for pattern: {pattern}. {e}")

        self._save_learned_patterns()
        logger.info(f"Updated learned patterns. Total: {len(self.learned_patterns)}")

    def get_dynamic_prompts(self) -> Dict[str, str]:
        """
        Generates dynamic prompt additions for agents based on learned patterns.
        """
        dynamic_prompts = {
            "price_agent": "",
            "review_agent": "",
            "seller_agent": "",
            "image_agent": ""
        }

        # Search the vector database for the most relevant patterns
        num_results = 5 # Example: get top 5 most similar patterns
        for agent_type in dynamic_prompts.keys():
            # Create a query embedding (e.g., based on the agent's role/goal)
            query_embedding = np.random.rand(self.embedding_dimension).astype('float32') # Placeholder
            D, I = self.index.search(np.array([query_embedding]), num_results) # Search the index
            
            # Add the most relevant patterns to the prompt
            for i in range(num_results):
                pattern_index = I[0][i]
                if pattern_index < len(self.learned_patterns):
                    pattern = self.learned_patterns[pattern_index]
                    heuristic_desc = pattern.get("heuristic", "an unidentified pattern")
                    if pattern["type"] == "price_manipulation" and agent_type == "price_agent":
                        dynamic_prompts["price_agent"] += f"\n- **Prioritize**: Look for '{heuristic_desc}' as it's a highly rewarded fraud pattern."
                    elif pattern["type"] == "fake_reviews" and agent_type == "review_agent":
                        dynamic_prompts["review_agent"] += f"\n- **Prioritize**: Investigate '{heuristic_desc}' as it's a highly rewarded fraud pattern."
                    elif pattern["type"] == "seller_behavior_anomaly" and agent_type == "seller_agent":
                        dynamic_prompts["seller_agent"] += f"\n- **Prioritize**: Pay close attention to '{heuristic_desc}' as it's a highly rewarded fraud pattern."
                    elif pattern["type"] == "image_manipulation" and agent_type == "image_agent":
                        dynamic_prompts["image_agent"] += f"\n- **Prioritize**: Scrutinize '{heuristic_desc}' as it's a highly rewarded fraud pattern."
        
        return dynamic_prompts

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example usage:
    # 1. Simulate some exploratory signals being logged
    # (This would normally happen via the agents using the log_pattern_memory tool)
    if not os.path.exists(PATTERN_MEMORY_FILE):
        with open(PATTERN_MEMORY_FILE, 'w') as f:
            json.dump([], f)

    with open(PATTERN_MEMORY_FILE, 'w') as f:
        json.dump([
            {"type": "price_manipulation", "product_id": "prod_fraud_1", "seller_id": "seller_fraud_1", "heuristic": "price_exact_match_6_months_ago", "timestamp": "2025-01-01T12:00:00Z"},
            {"type": "fake_reviews", "product_id": "prod_fraud_2", "seller_id": "seller_fraud_2", "heuristic": "burst_review_pattern", "timestamp": "2025-01-02T12:00:00Z"},
            {"type": "seller_behavior_anomaly", "product_id": "prod_clean_1", "seller_id": "seller_clean_1", "heuristic": "sudden_category_switch", "timestamp": "2025-01-03T12:00:00Z"},
            {"type": "image_manipulation", "product_id": "prod_test_3", "seller_id": "seller_test_3", "heuristic": "high_compression_artifacts", "timestamp": "2025-01-04T12:00:00Z"}
        ], f, indent=4)

    learner = ReinforcementLearner()
    learner.learn_from_patterns()
    
    dynamic_prompts = learner.get_dynamic_prompts()
    print("\nDynamic Prompts for Agents:")
    for agent_type, prompt_additions in dynamic_prompts.items():
        if prompt_additions:
            print(f"--- {agent_type.replace('_', ' ').title()} ---")
            print(prompt_additions)
