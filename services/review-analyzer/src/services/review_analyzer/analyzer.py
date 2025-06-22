import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Download required NLTK data
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

logger = logging.getLogger(__name__)

class ReviewAnalyzer:
    """
    Analyzes reviews for authenticity using multiple detection techniques.
    """
    
    def __init__(self, similarity_threshold: float = 0.8, burst_window_hours: int = 24):
        """
        Initialize the ReviewAnalyzer.
        
        Args:
            similarity_threshold: Threshold for considering reviews as similar (0-1)
            burst_window_hours: Time window in hours to check for review bursts
        """
        self.similarity_threshold = similarity_threshold
        self.burst_window_hours = burst_window_hours
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.sia = SentimentIntensityAnalyzer()
        self.review_history = []  # In-memory storage, replace with DB in production
        
    def analyze_review(self, review_data: Dict) -> Dict:
        """
        Analyze a single review for authenticity.
        
        Args:
            review_data: Dictionary containing review data with keys:
                - text: Review text
                - reviewer_id: ID of the reviewer
                - timestamp: ISO format timestamp of the review
                - is_verified: Boolean indicating if purchase is verified
                - product_id: ID of the product being reviewed
                
        Returns:
            Dictionary containing analysis results
        """
        try:
            # 1. Text Uniqueness (40%)
            uniqueness_score = self._check_uniqueness(
                review_data['text'], 
                review_data['product_id']
            )
            
            # 2. Temporal Analysis (30%)
            timestamp_score = self._analyze_timing(
                review_data['timestamp'], 
                review_data['reviewer_id']
            )
            
            # 3. Verification Status (20%)
            verified_score = 1.0 if review_data.get('is_verified', False) else 0.5
            
            # 4. Sentiment Analysis (10%)
            sentiment_score = self._analyze_sentiment(review_data['text'])
            
            # Calculate final score (weighted average)
            final_score = (
                0.4 * uniqueness_score +
                0.3 * timestamp_score +
                0.2 * verified_score +
                0.1 * sentiment_score
            )
            
            # Store the review for future analysis
            self.review_history.append({
                'text': review_data['text'],
                'reviewer_id': review_data['reviewer_id'],
                'product_id': review_data['product_id'],
                'timestamp': review_data['timestamp'],
                'analysis': {
                    'uniqueness': uniqueness_score,
                    'temporal': timestamp_score,
                    'verified': verified_score,
                    'sentiment': sentiment_score,
                    'final_score': final_score
                }
            })
            
            return {
                'review_id': review_data.get('review_id'),
                'authenticity_score': final_score,
                'components': {
                    'uniqueness': uniqueness_score,
                    'temporal': timestamp_score,
                    'verified': verified_score,
                    'sentiment': sentiment_score
                },
                'is_suspicious': final_score < 0.5,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing review: {str(e)}", exc_info=True)
            raise
    
    def _check_uniqueness(self, text: str, product_id: str) -> float:
        """Check how unique the review text is compared to existing reviews."""
        try:
            # Get existing reviews for this product
            product_reviews = [
                r['text'] for r in self.review_history 
                if r['product_id'] == product_id
            ]
            
            if not product_reviews:
                return 1.0  # First review for this product
                
            # Add current review for comparison
            all_reviews = product_reviews + [text]
            
            # Create TF-IDF matrix
            tfidf_matrix = self.vectorizer.fit_transform(all_reviews)
            
            # Calculate cosine similarity between current review and all others
            similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])
            
            # Get max similarity score (how similar is this to the most similar review)
            max_similarity = np.max(similarities) if similarities.size > 0 else 0.0
            
            # Convert to uniqueness score (higher = more unique)
            return 1.0 - min(max_similarity, self.similarity_threshold) / self.similarity_threshold
            
        except Exception as e:
            logger.error(f"Error in uniqueness check: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _analyze_timing(self, timestamp: str, reviewer_id: str) -> float:
        """Analyze the timing of the review for suspicious patterns."""
        try:
            review_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            window_start = review_time - timedelta(hours=self.burst_window_hours)
            
            # Count reviews by this user in the time window
            recent_reviews = [
                r for r in self.review_history
                if (r['reviewer_id'] == reviewer_id and 
                    datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) >= window_start)
            ]
            
            # More than 3 reviews in the window is suspicious
            review_count = len(recent_reviews)
            if review_count == 0:
                return 1.0  # No recent reviews
                
            # Score decreases as number of recent reviews increases
            return max(0.0, 1.0 - (min(review_count, 10) / 10))
            
        except Exception as e:
            logger.error(f"Error in timing analysis: {str(e)}")
            return 0.5  # Neutral score on error
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment and detect potential fake patterns."""
        try:
            # Get sentiment scores
            scores = self.sia.polarity_scores(text)
            
            # Very positive or very negative reviews might be suspicious
            if scores['compound'] >= 0.8 or scores['compound'] <= -0.8:
                return 0.5  # Slightly penalize extreme sentiments
                
            # Neutral to moderately positive reviews are considered more authentic
            return 1.0
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return 0.5  # Neutral score on error
