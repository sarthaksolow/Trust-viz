import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app, ReviewAnalyzer
from src.services.review_analyzer.analyzer import ReviewAnalyzer as CoreAnalyzer

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch('src.services.review_analyzer.analyzer.ReviewAnalyzer')
def test_analyze_review(mock_analyzer):
    """Test the review analysis endpoint."""
    # Setup mock
    mock_result = {
        'review_id': 'test123',
        'authenticity_score': 0.85,
        'is_suspicious': False,
        'components': {
            'uniqueness': 0.9,
            'temporal': 0.8,
            'verified': 1.0,
            'sentiment': 0.6
        },
        'analysis_timestamp': '2023-01-01T00:00:00.000000'
    }
    mock_analyzer.return_value.analyze_review.return_value = mock_result
    
    # Test data
    review_data = {
        "review_id": "test123",
        "text": "Great product! Works as expected.",
        "reviewer_id": "user123",
        "product_id": "prod456",
        "timestamp": "2023-01-01T00:00:00Z",
        "is_verified": True,
        "rating": 5
    }
    
    # Make request
    response = client.post("/analyze", json=review_data)
    
    # Assertions
    assert response.status_code == 200
    result = response.json()
    assert result["review_id"] == "test123"
    assert 0 <= result["authenticity_score"] <= 1.0
    assert isinstance(result["is_suspicious"], bool)
    assert "components" in result

@patch('src.services.review_analyzer.analyzer.ReviewAnalyzer')
def test_analyze_suspicious_review(mock_analyzer):
    """Test analysis of a suspicious review."""
    # Setup mock for suspicious review
    mock_result = {
        'review_id': 'suspicious123',
        'authenticity_score': 0.3,
        'is_suspicious': True,
        'components': {
            'uniqueness': 0.1,
            'temporal': 0.2,
            'verified': 0.5,
            'sentiment': 0.5
        },
        'analysis_timestamp': '2023-01-01T00:00:00.000000'
    }
    mock_analyzer.return_value.analyze_review.return_value = mock_result
    
    # Test data for suspicious review
    review_data = {
        "review_id": "suspicious123",
        "text": "Amazing! Perfect! Best ever! Must buy! 5 stars!",  # Overly positive
        "reviewer_id": "user789",
        "product_id": "prod456",
        "timestamp": "2023-01-01T00:00:00Z",
        "is_verified": False,
        "rating": 5
    }
    
    # Make request
    response = client.post("/analyze", json=review_data)
    
    # Assertions
    assert response.status_code == 200
    result = response.json()
    assert result["is_suspicious"] is True
    assert result["authenticity_score"] < 0.5

def test_uniqueness_check():
    """Test the uniqueness check functionality."""
    analyzer = CoreAnalyzer()
    
    # First review should be unique
    review1 = {
        'text': 'This is a unique review for testing.',
        'reviewer_id': 'user1',
        'product_id': 'prod1',
        'timestamp': '2023-01-01T00:00:00Z',
        'is_verified': True
    }
    result1 = analyzer.analyze_review(review1)
    assert result1['components']['uniqueness'] == 1.0  # Should be unique
    
    # Identical review should have low uniqueness
    review2 = {
        'text': 'This is a unique review for testing.',
        'reviewer_id': 'user2',
        'product_id': 'prod1',
        'timestamp': '2023-01-01T00:01:00Z',
        'is_verified': True
    }
    result2 = analyzer.analyze_review(review2)
    assert result2['components']['uniqueness'] < 0.5  # Should be low due to duplication

def test_temporal_analysis():
    """Test the temporal analysis for review bursts."""
    analyzer = CoreAnalyzer(burst_window_hours=24)
    
    # First review - should be fine
    review1 = {
        'text': 'First review',
        'reviewer_id': 'user1',
        'product_id': 'prod1',
        'timestamp': '2023-01-01T00:00:00Z',
        'is_verified': True
    }
    result1 = analyzer.analyze_review(review1)
    assert result1['components']['temporal'] == 1.0  # No recent reviews
    
    # Multiple reviews in short time - should lower the score
    for i in range(2, 6):  # 5 total reviews from same user
        review = {
            'text': f'Review {i}',
            'reviewer_id': 'user1',
            'product_id': 'prod1',
            'timestamp': f'2023-01-01T00:{i:02d}:00Z',  # 1 minute apart
            'is_verified': True
        }
        result = analyzer.analyze_review(review)
    
    # The score should decrease with more reviews
    assert result['components']['temporal'] < 0.5
