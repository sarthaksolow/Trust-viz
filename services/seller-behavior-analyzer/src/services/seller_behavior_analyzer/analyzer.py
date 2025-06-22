import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib

logger = logging.getLogger(__name__)

class SellerBehaviorAnalyzer:
    """
    Analyzes seller behavior to detect potential fraud or suspicious activities.
    """
    
    def __init__(
        self,
        account_age_threshold_days: int = 30,
        growth_rate_threshold: float = 10.0,
        description_similarity_threshold: float = 0.8,
        max_complaints_threshold: int = 5,
        high_refund_rate_threshold: float = 0.3
    ):
        """
        Initialize the SellerBehaviorAnalyzer with configurable thresholds.
        
        Args:
            account_age_threshold_days: Minimum account age in days to be considered established
            growth_rate_threshold: Maximum allowed product growth rate (products/day) before flagging
            description_similarity_threshold: Similarity threshold for detecting reused descriptions
            max_complaints_threshold: Maximum number of complaints before penalizing
            high_refund_rate_threshold: Refund rate above which to penalize (0.0-1.0)
        """
        self.account_age_threshold_days = account_age_threshold_days
        self.growth_rate_threshold = growth_rate_threshold
        self.description_similarity_threshold = description_similarity_threshold
        self.max_complaints_threshold = max_complaints_threshold
        self.high_refund_rate_threshold = high_refund_rate_threshold
        
        # Initialize TF-IDF vectorizer for description similarity
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # In-memory storage (replace with database in production)
        self.seller_data = {}
        self.product_descriptions = {}
    
    def analyze_seller(self, seller_data: Dict) -> Dict:
        """
        Analyze a seller's behavior and return a trust score.
        
        Args:
            seller_data: Dictionary containing seller information and metrics
            
        Returns:
            Dictionary containing analysis results and scores
        """
        try:
            seller_id = seller_data['seller_id']
            
            # 1. Account Age Analysis (20% weight)
            account_age_score = self._analyze_account_age(
                seller_data.get('account_created_at'),
                seller_data.get('first_listing_date')
            )
            
            # 2. Growth Rate Analysis (30% weight)
            growth_rate_score = self._analyze_growth_rate(
                seller_id,
                seller_data.get('products'),
                seller_data.get('product_creation_dates', [])
            )
            
            # 3. Description Reuse Analysis (20% weight)
            description_reuse_score = self._analyze_description_reuse(
                seller_id,
                seller_data.get('products', [])
            )
            
            # 4. Complaint Analysis (30% weight)
            complaint_score = self._analyze_complaints(
                seller_data.get('complaints', []),
                seller_data.get('total_orders', 1)
            )
            
            # Calculate final score (weighted average)
            final_score = (
                0.2 * account_age_score +
                0.3 * growth_rate_score +
                0.2 * description_reuse_score +
                0.3 * complaint_score
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(final_score)
            
            # Store seller data for future analysis
            self._update_seller_data(seller_id, seller_data, final_score)
            
            return {
                'seller_id': seller_id,
                'behavior_score': final_score,
                'risk_level': risk_level,
                'components': {
                    'account_age': account_age_score,
                    'growth_rate': growth_rate_score,
                    'description_reuse': description_reuse_score,
                    'complaint_analysis': complaint_score
                },
                'is_high_risk': risk_level in ['high', 'very_high'],
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing seller {seller_id}: {str(e)}", exc_info=True)
            raise
    
    def _analyze_account_age(self, account_created_at: str, first_listing_date: str = None) -> float:
        """Analyze the seller's account age and history."""
        if not account_created_at:
            return 0.0  # Missing data is suspicious
            
        try:
            created_date = datetime.fromisoformat(account_created_at.replace('Z', '+00:00'))
            account_age_days = (datetime.utcnow() - created_date).days
            
            # New accounts are considered higher risk
            if account_age_days < 1:
                return 0.1
            elif account_age_days < self.account_age_threshold_days:
                # Linearly scale from 0.1 to 1.0 over the threshold period
                return min(1.0, 0.1 + (0.9 * (account_created_at / self.account_age_threshold_days)))
            return 1.0
            
        except (ValueError, TypeError):
            logger.warning(f"Invalid date format: {account_created_at}")
            return 0.5  # Neutral score for invalid data
    
    def _analyze_growth_rate(self, seller_id: str, products: List[Dict] = None, 
                           creation_dates: List[str] = None) -> float:
        """Analyze the rate at which products are being added."""
        if not products or not creation_dates or len(creation_dates) < 2:
            return 1.0  # Not enough data to determine growth rate
            
        try:
            # Parse creation dates
            dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in creation_dates]
            dates.sort()
            
            # Calculate time delta in days
            time_span = (dates[-1] - dates[0]).days or 1  # Avoid division by zero
            num_products = len(products)
            growth_rate = num_products / time_span
            
            # Normalize score based on threshold
            if growth_rate <= 0:
                return 1.0
            elif growth_rate >= self.growth_rate_threshold:
                return 0.1
            else:
                # Linearly scale from 1.0 to 0.1 as growth rate approaches threshold
                return 1.0 - (0.9 * (growth_rate / self.growth_rate_threshold))
                
        except Exception as e:
            logger.error(f"Error calculating growth rate: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _analyze_description_reuse(self, seller_id: str, products: List[Dict]) -> float:
        """Check for reused product descriptions."""
        if not products or len(products) < 2:
            return 1.0  # Not enough products to compare
            
        try:
            # Extract descriptions
            descriptions = [p.get('description', '') for p in products if p.get('description')]
            
            if len(descriptions) < 2:
                return 1.0  # Not enough descriptions to compare
            
            # Calculate TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform(descriptions)
            
            # Calculate cosine similarity between all pairs of descriptions
            similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # Get upper triangle (avoid self-comparison and duplicates)
            similarity_scores = []
            for i in range(len(descriptions)):
                for j in range(i + 1, len(descriptions)):
                    similarity_scores.append(similarity_matrix[i][j])
            
            if not similarity_scores:
                return 1.0
                
            # Get max similarity score
            max_similarity = max(similarity_scores)
            
            # Calculate score (lower similarity is better)
            if max_similarity >= self.description_similarity_threshold:
                # Linearly scale from 0.1 to 1.0 based on similarity
                return max(0.1, 1.0 - (0.9 * (
                    (max_similarity - self.description_similarity_threshold) / 
                    (1.0 - self.description_similarity_threshold)
                )))
            return 1.0
            
        except Exception as e:
            logger.error(f"Error analyzing description reuse: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _analyze_complaints(self, complaints: List[Dict], total_orders: int) -> float:
        """Analyze complaints and refund rates."""
        if not complaints:
            return 1.0  # No complaints is good
            
        try:
            # Calculate complaint rate
            num_complaints = len(complaints)
            complaint_ratio = num_complaints / max(1, total_orders)
            
            # Calculate severity-weighted complaint score
            severity_scores = [
                self._get_complaint_severity(c.get('type', 'low')) 
                for c in complaints
            ]
            avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 0
            
            # Calculate refund rate if available
            refunds = [c for c in complaints if c.get('result') == 'refunded']
            refund_rate = len(refunds) / max(1, total_orders)
            
            # Calculate base score from complaint count
            if num_complaints == 0:
                count_score = 1.0
            elif num_complaints >= self.max_complaints_threshold:
                count_score = 0.1
            else:
                # Linearly scale from 1.0 to 0.1
                count_score = 1.0 - (0.9 * (num_complaints / self.max_complaints_threshold))
            
            # Adjust for severity
            severity_adjusted_score = count_score * (1.0 - (avg_severity * 0.5))
            
            # Adjust for refund rate
            if refund_rate >= self.high_refund_rate_threshold:
                refund_penalty = 0.5 * (refund_rate / self.high_refund_rate_threshold)
                severity_adjusted_score *= (1.0 - refund_penalty)
            
            return max(0.1, min(1.0, severity_adjusted_score))
            
        except Exception as e:
            logger.error(f"Error analyzing complaints: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _get_complaint_severity(self, complaint_type: str) -> float:
        """Map complaint type to severity score (0.0-1.0)."""
        severity_map = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'fraud': 1.0,
            'scam': 1.0
        }
        return severity_map.get(complaint_type.lower(), 0.5)
    
    def _determine_risk_level(self, score: float) -> str:
        """Convert numerical score to risk level."""
        if score >= 0.8:
            return 'very_low'
        elif score >= 0.6:
            return 'low'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'high'
        else:
            return 'very_high'
    
    def _update_seller_data(self, seller_id: str, seller_data: Dict, score: float):
        """Update internal seller data store."""
        self.seller_data[seller_id] = {
            'last_analyzed': datetime.utcnow().isoformat(),
            'score': score,
            'product_count': len(seller_data.get('products', [])),
            'metadata': {
                'has_high_risk_products': any(
                    p.get('is_high_risk', False) 
                    for p in seller_data.get('products', [])
                )
            }
        }
        
        # Store product descriptions for future analysis
        for product in seller_data.get('products', []):
            if 'product_id' in product and 'description' in product:
                self.product_descriptions[product['product_id']] = product['description']
