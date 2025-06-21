# services/perceptual-ai/src/main.py

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, HttpUrl
from PIL import Image, ImageFilter
import imagehash
import numpy as np
from typing import Dict, Optional
import json
import os
import logging
from confluent_kafka import Producer
import requests
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PerceptualAI")

app = FastAPI()

class ImageAnalysisRequest(BaseModel):
    product_id: str
    product_image_url: HttpUrl
    seller_id: Optional[str] = None

class DinoHash:
    def __init__(self):
        self.hash_size = 16  # Using larger hash for more detail

    def compute_hash(self, image: Image.Image) -> Dict[str, str]:
        """
        Compute multiple perceptual hashes for robust comparison
        """
        try:
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Compute different types of hashes
            avg_hash = str(imagehash.average_hash(image, self.hash_size))
            diff_hash = str(imagehash.dhash(image, self.hash_size))
            perc_hash = str(imagehash.phash(image, self.hash_size))
            wave_hash = str(imagehash.whash(image, self.hash_size))

            # Create hash signature
            hash_signature = {
                'avg_hash': avg_hash,    # Overall structure
                'diff_hash': diff_hash,  # Gradient patterns
                'perc_hash': perc_hash,  # Frequency domain
                'wave_hash': wave_hash   # Color patterns
            }

            logger.info("Successfully computed DinoHash signature")
            return hash_signature

        except Exception as e:
            logger.error(f"Error computing DinoHash: {e}")
            raise ValueError(f"Failed to compute image hash: {str(e)}")

    def calculate_similarity(self, hash1: Dict[str, str], hash2: Dict[str, str]) -> float:
        """
        Calculate weighted similarity between two hash signatures
        """
        try:
            # Weights for different hash types
            weights = {
                'avg_hash': 0.3,   # Overall structure importance
                'diff_hash': 0.3,  # Gradient patterns importance
                'perc_hash': 0.2,  # Frequency domain importance
                'wave_hash': 0.2   # Color patterns importance
            }

            total_similarity = 0.0
            for hash_type, weight in weights.items():
                # Convert hex strings to binary and calculate Hamming distance
                h1 = int(hash1[hash_type], 16)
                h2 = int(hash2[hash_type], 16)
                hamming_distance = bin(h1 ^ h2).count('1')
                
                # Convert distance to similarity score
                max_distance = self.hash_size * self.hash_size
                similarity = 1 - (hamming_distance / max_distance)
                
                # Add weighted similarity
                total_similarity += similarity * weight

            return total_similarity

        except Exception as e:
            logger.error(f"Error calculating hash similarity: {e}")
            return 0.0

# Initialize DinoHash
dino_hash = DinoHash()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
KAFKA_TOPIC_IMAGE_SCORE = os.getenv('KAFKA_TOPIC_IMAGE_SCORE', 'image-score')

producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'perceptual-ai-producer'
})

def delivery_report(err, msg):
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
    else:
        logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

async def download_image(image_url: str) -> Image.Image:
    """Download and validate image from URL"""
    try:
        response = requests.get(str(image_url), timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        if image.size[0] < 10 or image.size[1] < 10:
            raise ValueError("Image too small")
        
        return image

    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analyze")
async def analyze(request: ImageAnalysisRequest):
    try:
        logger.info(f"Processing image analysis for product {request.product_id}")

        # Download and validate image
        image = await download_image(str(request.product_image_url))
        
        # Generate DinoHash signature
        hash_signature = dino_hash.compute_hash(image)
        
        # For now, using placeholder comparison (will be replaced with Redis storage)
        analysis_result = {
            'product_id': request.product_id,
            'image_size': image.size,
            'hash_signature': hash_signature,
            'analysis_stage': 'dinohash_complete'
        }

        # Send results to Kafka
        producer.produce(
            KAFKA_TOPIC_IMAGE_SCORE,
            key=request.product_id.encode('utf-8'),
            value=json.dumps(analysis_result).encode('utf-8'),
            callback=delivery_report
        )
        producer.flush()

        return analysis_result

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Perceptual AI",
        "stage": "dinohash_implemented"
    }

@app.on_event("shutdown")
async def shutdown_event():
    producer.flush()