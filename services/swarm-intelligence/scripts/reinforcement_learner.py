import json
import os
import logging
from typing import Dict, List, Any
import random
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

PATTERN_MEMORY_FILE = "pattern_memory.json"
# Placeholder for confirmed fraud outcomes from Trust Ledger
CONFIRMED_FRAUD_OUTCOMES = [
    {"product_id": "prod_fraud_1", "seller_id": "seller_fraud_1", "is_fraud": True, "fraud_type": "price_manipulation"},
    {"product_id": "prod_fraud_2", "seller_id": "seller_fraud_2", "is_fraud": True, "fraud_type": "fake_reviews"},
    {"product_id": "prod_clean_1", "seller_id": "seller_clean_1", "is_fraud": False},
]

class ReinforcementLearner:
    def __init__(self, embedding_dimension: int = 128):
        self.embedding_dimension = embedding_dimension
        self.learned_patterns = []
        self.pattern_embeddings = []
        self._load_learned_patterns()
        logger.info(f"ReinforcementLearner initialized. Loaded {len(self.learned_patterns)} learned patterns.")

    def _pattern_to_embedding(self, pattern: Dict) -> np.ndarray:
        """Converts a pattern dictionary to a numerical embedding (placeholder)."""
        # Simple embedding based on pattern characteristics
        pattern_string = json.dumps(pattern, sort_keys=True)
        hash_value = hash(pattern_string) % (10**8)
        
        # Create a more meaningful embedding
        embedding = np.random.RandomState(hash_value).rand(self.embedding_dimension).astype('float32')
        
        # Inject some pattern-specific information
        if "price_manipulation" in pattern.get("type", ""):
            embedding[0] = 0.9
        elif "fake_reviews" in pattern.get("type", ""):
            embedding[1] = 0.9
        elif "seller_behavior" in pattern.get("type", ""):
            embedding[2] = 0.9
        elif "image_manipulation" in pattern.get("type", ""):
            embedding[3] = 0.9
        
        # Add reward score influence
        reward_score = pattern.get("reward_score", 0)
        if reward_score > 0:
            embedding[4] = min(1.0, reward_score / 10.0)
            
        return embedding

    def _load_learned_patterns(self):
        """Loads learned patterns from persistent storage."""
        learned_patterns_path = "learned_patterns.json"
        if os.path.exists(learned_patterns_path):
            try:
                with open(learned_patterns_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.learned_patterns = data
                    else:
                        self.learned_patterns = []
                    
                    # Regenerate embeddings
                    self.pattern_embeddings = [self._pattern_to_embedding(p) for p in self.learned_patterns]
                    logger.info(f"Loaded {len(self.learned_patterns)} learned patterns.")
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load learned patterns: {e}. Starting with empty patterns.")
                self.learned_patterns = []
                self.pattern_embeddings = []
        else:
            self.learned_patterns = []
            self.pattern_embeddings = []

    def _save_learned_patterns(self):
        """Saves learned patterns to persistent storage."""
        learned_patterns_path = "learned_patterns.json"
        try:
            with open(learned_patterns_path, 'w') as f:
                json.dump(self.learned_patterns, f, indent=4)
            logger.info(f"Saved {len(self.learned_patterns)} learned patterns.")
        except Exception as e:
            logger.error(f"Failed to save learned patterns: {e}")

    def _read_exploratory_signals(self) -> List[Dict]:
        """Reads all exploratory signals from pattern_memory.json."""
        if not os.path.exists(PATTERN_MEMORY_FILE):
            return []
        try:
            with open(PATTERN_MEMORY_FILE, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding {PATTERN_MEMORY_FILE}: {e}")
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

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot_product / (norm_a * norm_b)

    def learn_from_patterns(self):
        """
        Reads exploratory signals and confirmed fraud outcomes,
        rewards useful patterns, and updates learned patterns.
        """
        exploratory_signals = self._read_exploratory_signals()
        logger.info(f"Read {len(exploratory_signals)} exploratory signals.")

        new_useful_patterns = []

        for signal in exploratory_signals:
            signal_type = signal.get("type", "unknown")
            product_id = signal.get("product_id")
            seller_id = signal.get("seller_id")
            heuristic = signal.get("heuristic", "unknown_heuristic")
            
            # Check if this signal correlates with a confirmed fraud outcome
            confirmed_outcomes = self._get_confirmed_fraud_outcomes(product_id=product_id, seller_id=seller_id)
            
            is_useful = False
            fraud_type_match = False
            
            for outcome in confirmed_outcomes:
                if outcome.get("is_fraud"):
                    is_useful = True
                    if outcome.get("fraud_type") == signal_type:
                        fraud_type_match = True
                        break
            
            if is_useful:
                # Calculate reward based on accuracy
                reward_multiplier = 2.0 if fraud_type_match else 1.0
                
                # Check if we already have a similar pattern
                existing_pattern = None
                for existing in self.learned_patterns:
                    if (existing.get("type") == signal_type and 
                        existing.get("heuristic") == heuristic):
                        existing_pattern = existing
                        break
                
                if existing_pattern:
                    # Update existing pattern
                    existing_pattern["reward_score"] = existing_pattern.get("reward_score", 0) + reward_multiplier
                    existing_pattern["last_rewarded"] = datetime.now().isoformat()
                    existing_pattern["usage_count"] = existing_pattern.get("usage_count", 0) + 1
                    logger.info(f"Updated existing pattern: {existing_pattern}")
                else:
                    # Create new pattern
                    pattern = {
                        "type": signal_type,
                        "heuristic": heuristic,
                        "reward_score": reward_multiplier,
                        "last_rewarded": datetime.now().isoformat(),
                        "decay_factor": 0.95,
                        "usage_count": 1,
                        "confidence": 0.8 if fraud_type_match else 0.6
                    }
                    new_useful_patterns.append(pattern)
                    logger.info(f"Created new useful pattern: {pattern}")
            else:
                # Explore: occasionally add patterns even if not immediately useful
                if random.random() < 0.05:  # 5% exploration rate
                    pattern = {
                        "type": signal_type,
                        "heuristic": f"exploratory_{heuristic}",
                        "reward_score": 0.1,
                        "last_rewarded": datetime.now().isoformat(),
                        "decay_factor": 0.9,
                        "usage_count": 1,
                        "confidence": 0.3
                    }
                    new_useful_patterns.append(pattern)
                    logger.info(f"Added exploratory pattern: {pattern}")

        # Add new patterns
        for new_pattern in new_useful_patterns:
            self.learned_patterns.append(new_pattern)
            self.pattern_embeddings.append(self._pattern_to_embedding(new_pattern))

        # Decay rewards of existing patterns
        current_time = datetime.now()
        for pattern in self.learned_patterns:
            if "last_rewarded" in pattern:
                try:
                    last_rewarded = datetime.fromisoformat(pattern["last_rewarded"])
                    time_since_reward = current_time - last_rewarded
                    decay_factor = pattern.get("decay_factor", 0.9)
                    
                    # Monthly decay
                    months_since_reward = time_since_reward.days / 30.0
                    decay_amount = pattern["reward_score"] * (1 - decay_factor) * months_since_reward
                    pattern["reward_score"] = max(0.1, pattern["reward_score"] - decay_amount)
                    
                    # Remove patterns with very low scores
                    if pattern["reward_score"] < 0.05 and pattern.get("usage_count", 0) == 0:
                        self.learned_patterns.remove(pattern)
                        logger.info(f"Removed low-value pattern: {pattern}")
                        
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing pattern decay: {e}")

        # Regenerate embeddings after modifications
        self.pattern_embeddings = [self._pattern_to_embedding(p) for p in self.learned_patterns]
        
        self._save_learned_patterns()
        logger.info(f"Learning complete. Total patterns: {len(self.learned_patterns)}")

    def get_dynamic_prompts(self) -> Dict[str, str]:
        """
        Generates dynamic prompt additions for agents based on learned patterns.
        """
        dynamic_prompts = {
            "price_agent": "",
            "review_agent": "",
            "seller_agent": "",
            "image_agent": "",
            "anomaly_detection_agent": ""
        }

        # Sort patterns by reward score (highest first)
        sorted_patterns = sorted(
            self.learned_patterns, 
            key=lambda x: x.get("reward_score", 0), 
            reverse=True
        )

        # Get top patterns for each agent type
        patterns_per_agent = 3
        
        for pattern in sorted_patterns[:patterns_per_agent * 5]:  # Get top patterns across all types
            pattern_type = pattern.get("type", "")
            heuristic = pattern.get("heuristic", "unknown")
            reward_score = pattern.get("reward_score", 0)
            confidence = pattern.get("confidence", 0)
            
            if reward_score < 0.5:  # Skip low-reward patterns
                continue
                
            prompt_addition = f"\n- **High Priority**: Look for '{heuristic}' patterns (confidence: {confidence:.2f}, effectiveness: {reward_score:.2f})"
            
            if "price_manipulation" in pattern_type or "price" in pattern_type:
                if len(dynamic_prompts["price_agent"]) < 300:  # Limit prompt length
                    dynamic_prompts["price_agent"] += prompt_addition
            elif "fake_reviews" in pattern_type or "review" in pattern_type:
                if len(dynamic_prompts["review_agent"]) < 300:
                    dynamic_prompts["review_agent"] += prompt_addition
            elif "seller_behavior" in pattern_type or "seller" in pattern_type:
                if len(dynamic_prompts["seller_agent"]) < 300:
                    dynamic_prompts["seller_agent"] += prompt_addition
            elif "image_manipulation" in pattern_type or "image" in pattern_type:
                if len(dynamic_prompts["image_agent"]) < 300:
                    dynamic_prompts["image_agent"] += prompt_addition
            elif "anomaly" in pattern_type:
                if len(dynamic_prompts["anomaly_detection_agent"]) < 300:
                    dynamic_prompts["anomaly_detection_agent"] += prompt_addition

        # Add general insights if we have learned patterns
        if self.learned_patterns:
            total_patterns = len(self.learned_patterns)
            avg_reward = sum(p.get("reward_score", 0) for p in self.learned_patterns) / total_patterns
            
            general_insight = f"\n- **System Insight**: Analysis based on {total_patterns} learned patterns (avg effectiveness: {avg_reward:.2f})"
            
            for agent_type in dynamic_prompts:
                if len(dynamic_prompts[agent_type]) < 200:
                    dynamic_prompts[agent_type] += general_insight

        return dynamic_prompts

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        if not self.learned_patterns:
            return {"total_patterns": 0, "pattern_types": {}, "avg_reward": 0}
        
        pattern_types = {}
        total_reward = 0
        
        for pattern in self.learned_patterns:
            pattern_type = pattern.get("type", "unknown")
            reward = pattern.get("reward_score", 0)
            
            if pattern_type not in pattern_types:
                pattern_types[pattern_type] = {"count": 0, "total_reward": 0}
            
            pattern_types[pattern_type]["count"] += 1
            pattern_types[pattern_type]["total_reward"] += reward
            total_reward += reward
        
        # Calculate averages
        for ptype in pattern_types:
            pattern_types[ptype]["avg_reward"] = pattern_types[ptype]["total_reward"] / pattern_types[ptype]["count"]
        
        return {
            "total_patterns": len(self.learned_patterns),
            "pattern_types": pattern_types,
            "avg_reward": total_reward / len(self.learned_patterns),
            "top_patterns": sorted(self.learned_patterns, key=lambda x: x.get("reward_score", 0), reverse=True)[:5]
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize pattern memory file with sample data
    if not os.path.exists(PATTERN_MEMORY_FILE):
        sample_signals = [
            {
                "type": "price_manipulation", 
                "product_id": "prod_fraud_1", 
                "seller_id": "seller_fraud_1", 
                "heuristic": "price_exact_match_6_months_ago", 
                "timestamp": "2025-01-01T12:00:00Z"
            },
            {
                "type": "fake_reviews", 
                "product_id": "prod_fraud_2", 
                "seller_id": "seller_fraud_2", 
                "heuristic": "burst_review_pattern", 
                "timestamp": "2025-01-02T12:00:00Z"
            },
            {
                "type": "seller_behavior_anomaly", 
                "product_id": "prod_clean_1", 
                "seller_id": "seller_clean_1", 
                "heuristic": "sudden_category_switch", 
                "timestamp": "2025-01-03T12:00:00Z"
            },
            {
                "type": "image_manipulation", 
                "product_id": "prod_test_3", 
                "seller_id": "seller_test_3", 
                "heuristic": "high_compression_artifacts", 
                "timestamp": "2025-01-04T12:00:00Z"
            }
        ]
        
        with open(PATTERN_MEMORY_FILE, 'w') as f:
            json.dump(sample_signals, f, indent=4)
        print(f"Created sample {PATTERN_MEMORY_FILE}")

    # Test the learner
    learner = ReinforcementLearner()
    
    print("\n=== Initial State ===")
    stats = learner.get_pattern_stats()
    print(f"Initial patterns: {stats}")
    
    print("\n=== Learning from Patterns ===")
    learner.learn_from_patterns()
    
    print("\n=== After Learning ===")
    stats = learner.get_pattern_stats()
    print(f"Learned patterns: {stats}")
    
    print("\n=== Dynamic Prompts ===")
    dynamic_prompts = learner.get_dynamic_prompts()
    for agent_type, prompt_additions in dynamic_prompts.items():
        if prompt_additions:
            print(f"\n--- {agent_type.replace('_', ' ').title()} ---")
            print(prompt_additions)