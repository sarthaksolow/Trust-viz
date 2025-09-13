import sys
import os
from pathlib import Path
from PIL import Image
import logging

# Add the parent directory of services/perceptual-ai/src to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services" / "perceptual-ai" / "src"))

from image_authenticity import ImageAuthenticityAnalyzer
from main import DinoHash # DinoHash is in main.py

# Setup logging for this debug script
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DebugImageAnalysis")

def run_debug_analysis():
    logger.info("🚀 Starting Debug Image Analysis")
    logger.info("===================================")

    test_images_dir = Path("test_images")

    if not test_images_dir.exists():
        logger.error("❌ Error: test_images directory not found. Please ensure it exists.")
        return

    seller_image_path = test_images_dir / "valid_img_walmart.png"
    brand_image_path = test_images_dir / "sus_img_walmart.png" # Using a specific brand image for direct testing

    if not seller_image_path.exists():
        logger.error(f"❌ Error: Seller image not found at {seller_image_path}")
        return
    if not brand_image_path.exists():
        logger.error(f"❌ Error: Brand image not found at {brand_image_path}")
        return

    try:
        seller_image = Image.open(seller_image_path).convert('RGB')
        brand_image = Image.open(brand_image_path).convert('RGB')
        
        logger.info(f"Loaded seller image: {seller_image_path}")
        logger.info(f"Loaded brand image: {brand_image_path}")

        dino_hash_instance = DinoHash()
        image_analyzer = ImageAuthenticityAnalyzer(dino_hash_instance=dino_hash_instance, hash_size=dino_hash_instance.hash_size)

        logger.info("Performing authenticity analysis...")
        results = image_analyzer.analyze_image_authenticity(
            seller_image=seller_image,
            brand_images=[brand_image],
            brand_image_urls=[str(brand_image_path)] # Pass URL for closest_brand_image
        )

        logger.info("\n📊 Analysis Results:")
        logger.info("==================")
        logger.info(f"✅ Final Authenticity Score: {results.get('score', 0):.2f}/1.00")
        logger.info("\n🔍 Detailed Analysis:")
        logger.info(f"- Hash Match Score: {results.get('details', {}).get('hash_match_score', 0):.2f}")
        logger.info(f"- Semantic Similarity: {results.get('details', {}).get('semantic_similarity', 0):.2f}")
        logger.info(f"- Quality Score: {results.get('details', {}).get('quality_score', 0):.2f}")
        logger.info(f"- Is Blurry: {results.get('details', {}).get('is_blurry')}")
        logger.info(f"- Matches Brand: {results.get('details', {}).get('matches_brand')}")
        logger.info(f"- Closest Brand Image: {results.get('closest_brand_image')}")

        if results.get('score', 0) < 0.5:
            logger.info("\n❌ RESULT: HIGH RISK - This product appears to be counterfeit")
        elif results.get('score', 0) < 0.7:
            logger.info("\n⚠️ RESULT: MEDIUM RISK - This product shows signs of being suspicious")
        else:
            logger.info("\n✅ RESULT: LOW RISK - This product appears to be authentic")

    except Exception as e:
        logger.error(f"❌ An error occurred during analysis: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_debug_analysis()
