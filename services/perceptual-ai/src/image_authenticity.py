import io
from typing import List, Dict, Any, Optional
from PIL import Image, ImageFilter
import io
from typing import List, Dict, Any, Optional
from PIL import Image, ImageFilter
import imagehash
import cv2
import numpy as np
import io
from typing import List, Dict, Any, Optional
from PIL import Image, ImageFilter
import imagehash
import cv2
import numpy as np
import logging

logger = logging.getLogger("ImageAuthenticityAnalyzer")

class ImageAuthenticityAnalyzer:
    """
    Analyzes the authenticity of product images by comparing them against verified brand images.
    Implements perceptual hashing, semantic similarity, and quality checks.
    """
    
    def __init__(self, dino_hash_instance, hash_size: int = 16, hash_threshold: int = 5, clip_similarity_threshold: float = 0.7):
        """
        Initialize the image analyzer.
        
        Args:
            dino_hash_instance: An instance of the DinoHash class for hash computations.
            hash_size: The size of the perceptual hash (e.g., 8, 16).
            hash_threshold: Maximum hamming distance for considering images as similar
            clip_similarity_threshold: Minimum similarity score (0-1) for considering images similar
        """
        self.dino_hash = dino_hash_instance
        self.hash_size = hash_size
        self.hash_threshold = hash_threshold
        self.clip_similarity_threshold = clip_similarity_threshold
        # logger.info(f"ImageAuthenticityAnalyzer initialized with hash_size={self.hash_size}") # Revert logging
    
    def _calculate_phash(self, image: Image.Image) -> imagehash.ImageHash:
        """Calculate perceptual hash of an image."""
        phash = imagehash.phash(image, hash_size=self.hash_size)
        # logger.debug(f"Calculated pHash: {phash}") # Revert logging
        return phash
    
    def _compare_hashes(self, hash1: imagehash.ImageHash, hash2: imagehash.ImageHash) -> float:
        """
        Compare two image hashes and return a similarity score (0-1).
        1 means identical, 0 means completely different.
        """
        hamming_distance = hash1 - hash2
        max_distance = self.hash_size * self.hash_size
        similarity = max(0, 1 - (hamming_distance / max_distance))
        # logger.debug(f"Comparing hashes: {hash1} vs {hash2}, Hamming distance: {hamming_distance}, Similarity: {similarity:.2f}") # Revert logging
        return similarity
    
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
        # logger.debug(f"Image quality check: Laplacian variance={laplacian_var:.2f}, Blur score={blur_score:.2f}") # Revert logging
        
        # Check for watermarks (simple check for now)
        # This is a placeholder - a real implementation would be more sophisticated
        watermark_score = 1.0  # Assume no watermark by default
        
        # Combine scores (equal weight for now)
        quality_score = (blur_score + watermark_score) / 2.0
        
        return quality_score
    
    def _calculate_semantic_similarity(self, seller_image: Image.Image, 
                                     brand_images: List[Image.Image]) -> float:
        """
        Calculate semantic similarity between seller's image and brand images using DinoHash's
        weighted similarity calculation.
        Returns the highest similarity score found.
        """
        seller_hash_signature = self.dino_hash.compute_hash(seller_image)
        best_similarity = 0.0
        
        for i, brand_img in enumerate(brand_images):
            brand_hash_signature = self.dino_hash.compute_hash(brand_img)
            similarity = self.dino_hash.calculate_similarity(seller_hash_signature, brand_hash_signature)
            best_similarity = max(best_similarity, similarity)
            # logger.debug(f"Semantic similarity with brand image {i}: {similarity:.2f}, Best so far: {best_similarity:.2f}") # Revert logging
            
            if best_similarity >= self.clip_similarity_threshold:
                # logger.debug(f"Semantic similarity threshold met: {best_similarity:.2f} >= {self.clip_similarity_threshold}") # Revert logging
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
            # logger.warning("No brand images provided for authenticity analysis.") # Revert logging
            raise ValueError("At least one brand image is required for comparison")
        
        # Initialize tracking for closest match
        best_similarity = 0.0
        closest_brand_index = 0
        
        # Calculate hash match score and find closest brand image
        seller_hash = self._calculate_phash(seller_image)
        
        for i, brand_img in enumerate(brand_images):
            brand_hash = self._calculate_phash(brand_img)
            similarity = self._compare_hashes(seller_hash, brand_hash)
            
            # Track the closest matching brand image
            if similarity > best_similarity:
                best_similarity = similarity
                closest_brand_index = i
                
            # No longer breaking early, as we want the best_similarity for hash_match
            # if similarity >= 0.95:  # Very close match
            #     hash_match = 1.0
            #     logger.debug(f"Hash match found (similarity >= 0.95) with brand image {i}")
            #     break
        
        # Set hash_match to the best similarity found
        hash_match = best_similarity
        # logger.debug(f"Final hash_match score set to best_similarity: {hash_match:.2f}") # Revert logging
        
        # Get the URL of the closest matching brand image if available
        closest_brand_url = None
        if brand_image_urls and len(brand_image_urls) > closest_brand_index:
            closest_brand_url = brand_image_urls[closest_brand_index]
        
        # Calculate semantic similarity (now using DinoHash's weighted similarity)
        semantic_similarity = self._calculate_semantic_similarity(seller_image, brand_images)
        
        # Check image quality
        quality_score = self._check_image_quality(seller_image)
        
        # Calculate final score using weighted average
        final_score = (0.5 * hash_match + 
                      0.3 * semantic_similarity + 
                      0.2 * quality_score)
        
        # logger.info(f"Final Authenticity Score: {final_score:.2f}") # Revert logging
        # logger.debug(f"Component scores: Hash Match={hash_match:.2f}, Semantic Similarity={semantic_similarity:.2f}, Quality={quality_score:.2f}") # Revert logging
        
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
