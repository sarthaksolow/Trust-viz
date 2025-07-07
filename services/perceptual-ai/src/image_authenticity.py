import io
from typing import List, Dict, Any, Optional
from PIL import Image, ImageFilter
import imagehash
import cv2
import numpy as np

class ImageAuthenticityAnalyzer:
    """
    Analyzes the authenticity of product images by comparing them against verified brand images.
    Implements perceptual hashing, semantic similarity, and quality checks.
    """
    
    def __init__(self, hash_threshold: int = 5, clip_similarity_threshold: float = 0.7):
        """
        Initialize the image analyzer.
        
        Args:
            hash_threshold: Maximum hamming distance for considering images as similar
            clip_similarity_threshold: Minimum similarity score (0-1) for considering images similar
        """
        self.hash_threshold = hash_threshold
        self.clip_similarity_threshold = clip_similarity_threshold
    
    def _calculate_phash(self, image: Image.Image) -> imagehash.ImageHash:
        """Calculate perceptual hash of an image."""
        return imagehash.phash(image)
    
    def _compare_hashes(self, hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> float:
        """
        Compare two image hashes and return a similarity score (0-1).
        1 means identical, 0 means completely different.
        """
        hamming_distance = hash1 - hash2
        # Normalize to 0-1 range where 1 is identical
        return max(0, 1 - (hamming_distance / 64.0))
    
    def _check_image_quality(self, image: Image.Image) -> float:
        """
        Check image quality by detecting blur and other artifacts.
        Returns a score between 0 (low quality) and 1 (high quality).
        """
        # Convert PIL Image to OpenCV format (numpy array)
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Check for blur using Laplacian variance
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normalize the blur score (higher variance = sharper image)
        # Values below 100 are typically considered blurry
        blur_score = min(1.0, laplacian_var / 100.0)
        
        # Check for watermarks (simple check for now)
        # This is a placeholder - a real implementation would be more sophisticated
        watermark_score = 1.0  # Assume no watermark by default
        
        # Combine scores (equal weight for now)
        quality_score = (blur_score + watermark_score) / 2.0
        
        return quality_score
    
    def _calculate_semantic_similarity(self, seller_image: Image.Image, 
                                     brand_images: List[Image.Image]) -> float:
        """
        Calculate semantic similarity between seller's image and brand images.
        For now, using perceptual hash as a placeholder for CLIP embeddings.
        Returns the highest similarity score found.
        """
        seller_hash = self._calculate_phash(seller_image)
        best_similarity = 0.0
        
        for brand_img in brand_images:
            brand_hash = self._calculate_phash(brand_img)
            similarity = self._compare_hashes(seller_hash, brand_hash)
            best_similarity = max(best_similarity, similarity)
            
            if best_similarity >= self.clip_similarity_threshold:
                break
                
        return best_similarity
    
    def analyze_image_authenticity(self, seller_image: Image.Image, 
                                 brand_images: List[Image.Image],
                                 brand_image_urls: List[str] = None) -> Dict[str, Any]:
        """
        Analyze the authenticity of a seller's product image.
        
        Args:
            seller_image: The product image provided by the seller
            brand_images: List of verified brand images to compare against
            brand_image_urls: Optional list of corresponding brand image URLs
            
        Returns:
            Dictionary containing analysis results and scores
        """
        if not brand_images:
            raise ValueError("At least one brand image is required for comparison")
        
        # Initialize tracking for closest match
        best_similarity = 0.0
        closest_brand_index = 0
        
        # Calculate hash match score and find closest brand image
        seller_hash = self._calculate_phash(seller_image)
        hash_match = 0.0
        
        for i, brand_img in enumerate(brand_images):
            brand_hash = self._calculate_phash(brand_img)
            similarity = self._compare_hashes(seller_hash, brand_hash)
            
            # Track the closest matching brand image
            if similarity > best_similarity:
                best_similarity = similarity
                closest_brand_index = i
                
            if similarity >= 0.95:  # Very close match
                hash_match = 1.0
                break
        
        # Get the URL of the closest matching brand image if available
        closest_brand_url = None
        if brand_image_urls and len(brand_image_urls) > closest_brand_index:
            closest_brand_url = brand_image_urls[closest_brand_index]
        
        # Calculate semantic similarity (placeholder for CLIP)
        semantic_similarity = self._calculate_semantic_similarity(seller_image, brand_images)
        
        # Check image quality
        quality_score = self._check_image_quality(seller_image)
        
        # Calculate final score using weighted average
        final_score = (0.5 * hash_match + 
                      0.3 * semantic_similarity + 
                      0.2 * quality_score)
        
        # Prepare results
        results = {
            'score': float(final_score),
            'match_found': final_score >= 0.7,  # Threshold can be adjusted
            'closest_brand_image': closest_brand_url,
            'details': {
                'hash_match_score': float(hash_match),
                'semantic_similarity': float(semantic_similarity),
                'quality_score': float(quality_score),
                'is_blurry': quality_score < 0.5,
                'is_tampered': False,  # Would be set by more advanced checks
                'matches_brand': hash_match > 0.8 or semantic_similarity > 0.7
            }
        }
        
        return results
