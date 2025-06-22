import requests
import os
from pathlib import Path

# Test configuration
PERCEPTUAL_AI_URL = "http://localhost:5003"  # Perceptual AI service runs on port 5003

def test_fake_product_detection():
    """Test the fake product detection with local test images."""
    print("🚀 Testing Fake Product Detection System with Local Images")
    print("====================================================")
    
    # Path to test images
    test_images_dir = Path("test_images")
    
    # Check if test images exist
    if not test_images_dir.exists():
        print("❌ Error: test_images directory not found. Please run download_test_images.py first.")
        return
    
    seller_image_path = test_images_dir / "seller.jpg"
    
    if not seller_image_path.exists():
        print(f"❌ Error: Seller image not found at {seller_image_path}")
        return
    
    # Get list of brand images (any jpg/png in the test_images directory except seller.jpg)
    brand_images = [f for f in test_images_dir.glob("*.jpg") if f.name != "seller.jpg"]
    
    if not brand_images:
        print("⚠️ No brand images found in test_images directory. Using a placeholder...")
        # Create a simple placeholder brand image
        from PIL import Image, ImageDraw
        placeholder_path = test_images_dir / "placeholder_brand.jpg"
        img = Image.new('RGB', (100, 100), color='white')
        d = ImageDraw.Draw(img)
        d.text((10, 45), "BRAND LOGO", fill='black')
        img.save(placeholder_path)
        brand_images = [placeholder_path]
    
    print(f"🔍 Analyzing {seller_image_path.name} against {len(brand_images)} brand images...")
    
    try:
        # Prepare files dictionary for the request
        files = {
            'seller_image': (seller_image_path.name, open(seller_image_path, 'rb'), 'image/jpeg')
        }
        
        # Add brand images
        for i, img_path in enumerate(brand_images):
            files[f'brand_images'] = (img_path.name, open(img_path, 'rb'), 'image/jpeg')
        
        # Make the request
        response = requests.post(
            f"{PERCEPTUAL_AI_URL}/analyze/authenticity",
            files=files
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
            
        result = response.json()
        
        print("\n📊 Analysis Results:")
        print("==================")
        
        # Display the authenticity analysis
        analysis = result.get('result', {})
        
        print(f"✅ Final Authenticity Score: {analysis.get('authenticity_score', 0):.2f}/1.00")
        print("\n🔍 Detailed Analysis:")
        print(f"- Hash Match Score: {analysis.get('hash_match_score', 0):.2f}")
        print(f"- Semantic Similarity: {analysis.get('semantic_similarity', 0):.2f}")
        print(f"- Quality Score: {analysis.get('quality_score', 0):.2f}")
        
        print("\n🚨 Potential Issues:")
        analysis_flags = analysis.get('analysis', {})
        if analysis_flags.get('is_blurry'):
            print("- ⚠️ Image appears blurry")
        if analysis_flags.get('is_tampered'):
            print("- ⚠️ Signs of image tampering detected")
        if not analysis_flags.get('matches_brand'):
            print("- ⚠️ Product doesn't match brand images")
        
        # Make a determination
        if analysis.get('authenticity_score', 0) < 0.5:
            print("\n❌ RESULT: HIGH RISK - This product appears to be counterfeit")
        elif analysis.get('authenticity_score', 0) < 0.7:
            print("\n⚠️ RESULT: MEDIUM RISK - This product shows signs of being suspicious")
        else:
            print("\n✅ RESULT: LOW RISK - This product appears to be authentic")
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    finally:
        # Close any open files
        for file in files.values():
            if hasattr(file[1], 'close'):
                file[1].close()

if __name__ == "__main__":
    test_fake_product_detection()
