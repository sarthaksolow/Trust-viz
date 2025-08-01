# services/perceptual-ai/src/main.py

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field
from PIL import Image, ImageFilter
import imagehash
import numpy as np
from typing import Dict, Optional, List, Union
import json
import os
import logging
from confluent_kafka import Producer
import requests
from io import BytesIO

# Import our image authenticity analyzer
from image_authenticity import ImageAuthenticityAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PerceptualAI")

app = FastAPI()

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

class ImageAnalysisRequest(BaseModel):
    product_id: str
    product_image_url: HttpUrl
    seller_id: Optional[str] = None
    brand_image_urls: Optional[List[HttpUrl]] = Field(
        default_factory=list, 
        description="List of verified brand image URLs for comparison"
    )

class ImageAuthenticityRequest(BaseModel):
    seller_image: Union[HttpUrl, bytes] = Field(
        ...,
        description="Either a URL to the seller's image or the image bytes"
    )
    brand_images: List[Union[HttpUrl, bytes]] = Field(
        default_factory=list,
        description="List of verified brand images (URLs or bytes) for comparison"
    )

# Initialize the image authenticity analyzer
image_analyzer = ImageAuthenticityAnalyzer()

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
    """
    Download and validate image from URL
    
    Args:
        image_url: URL of the image to download
        
    Returns:
        PIL.Image.Image: The downloaded and validated image in RGB mode
        
    Raises:
        ValueError: If the image cannot be downloaded or is invalid
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'image' not in content_type:
            raise ValueError(f"URL does not point to an image (content-type: {content_type})")
        
        # Open and validate image
        image = Image.open(BytesIO(response.content))
        image.verify()  # Verify that it is an image
        image = Image.open(BytesIO(response.content))  # Reopen after verify
        
        return image.convert('RGB')  # Ensure RGB mode
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to download image: {str(e)}")
    except (IOError, OSError) as e:
        raise ValueError(f"Invalid image data: {str(e)}")

@app.post("/analyze")
async def analyze(request: ImageAnalysisRequest):
    try:
        logger.info(f"Received analysis request for product: {request.product_id}")
        
        # Download the product image
        try:
            product_image = await download_image(str(request.product_image_url))
            logger.info(f"Successfully downloaded image from {request.product_image_url}")
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
        
        # Generate perceptual hashes
        try:
            hash_results = dino_hash.compute_hash(product_image)
            logger.info(f"Generated hashes for product {request.product_id}")
        except Exception as e:
            logger.error(f"Error generating hashes: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating image hashes: {str(e)}")
        
        # If brand images are provided, perform authenticity analysis
        authenticity_result = None
        if request.brand_image_urls:
            try:
                brand_images = []
                for url in request.brand_image_urls:
                    try:
                        brand_img = await download_image(str(url))
                        brand_images.append(brand_img)
                    except Exception as e:
                        logger.warning(f"Failed to download brand image {url}: {str(e)}")
                
                if brand_images:
                    authenticity_result = image_analyzer.analyze_image_authenticity(
                        seller_image=product_image,
                        brand_images=brand_images,
                        brand_image_urls=[str(url) for url in request.brand_image_urls] if request.brand_image_urls else None
                    )
            except Exception as e:
                logger.error(f"Error in authenticity analysis: {str(e)}", exc_info=True)
        
        # Prepare the result
        result = {
            "product_id": request.product_id,
            "seller_id": request.seller_id,
            "hashes": hash_results,
            "status": "success"
        }
        
        if authenticity_result:
            result["authenticity_analysis"] = authenticity_result
        
        # Send to Kafka if configured
        if KAFKA_BOOTSTRAP_SERVERS:
            try:
                producer.produce(
                    KAFKA_TOPIC_IMAGE_SCORE,
                    key=request.product_id.encode('utf-8'),
                    value=json.dumps(result).encode('utf-8'),
                    callback=delivery_report
                )
                producer.flush()
                logger.info(f"Sent results to Kafka for product {request.product_id}")
            except Exception as e:
                logger.error(f"Error sending to Kafka: {str(e)}")
                # Don't fail the request if Kafka is down
        
        return result
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze/authenticity")
async def analyze_authenticity(
    seller_image: UploadFile = File(...),
    brand_images: List[UploadFile] = File([]),
    image_url: Optional[str] = Form(None),
    brand_image_urls: Optional[List[str]] = Form([])
):
    """
    Analyze the authenticity of a seller's product image by comparing it with brand images.
    
    Args:
        seller_image: The product image file to analyze
        brand_images: List of verified brand image files for comparison
        image_url: Alternative to file upload - URL of the seller's image
        brand_image_urls: Alternative to file upload - URLs of brand images
    
    Returns:
        Dictionary containing authenticity analysis results
    """
    try:
        # Handle seller image (file upload or URL)
        if image_url:
            seller_img = await download_image(image_url)
        else:
            seller_img = Image.open(seller_image.file)
        
        # Handle brand images (file upload or URLs)
        brand_imgs = []
        
        # Add uploaded brand images
        for img_file in brand_images:
            try:
                img = Image.open(img_file.file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                brand_imgs.append(img)
            except Exception as e:
                logger.warning(f"Error processing brand image {img_file.filename}: {str(e)}")
        
        # Add brand images from URLs
        for url in brand_image_urls:
            try:
                img = await download_image(url)
                brand_imgs.append(img)
            except Exception as e:
                logger.warning(f"Error downloading brand image from {url}: {str(e)}")
        
        if not brand_imgs:
            raise HTTPException(
                status_code=400,
                detail="At least one brand image is required for authenticity analysis"
            )
        
        # Convert seller image to RGB if needed
        if seller_img.mode != 'RGB':
            seller_img = seller_img.convert('RGB')
        
        # Perform authenticity analysis
        result = image_analyzer.analyze_image_authenticity(seller_img, brand_imgs)
        
        return {
            "status": "success",
            "result": result
        }
        
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Error in authenticity analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

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
