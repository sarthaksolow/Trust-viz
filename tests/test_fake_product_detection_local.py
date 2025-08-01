import requests
import os
from pathlib import Path

# Test configuration
PERCEPTUAL_AI_URL = "http://localhost:8000"  # Perceptual AI service runs on port 5003

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
    brand_images.extend([f for f in test_images_dir.glob("*.png") if f.name != "seller.png"])
    
    if not brand_images:
        print("⚠️ No brand images found in test_images directory. Creating a placeholder...")
        # Create a simple placeholder brand image
        from PIL import Image, ImageDraw
        placeholder_path = test_images_dir / "brand_placeholder.jpg"
        img = Image.new('RGB', (200, 200), color='white')
        d = ImageDraw.Draw(img)
        d.text((50, 90), "BRAND LOGO", fill='black')
        img.save(placeholder_path)
        brand_images = [placeholder_path]
    
    print(f"🔍 Analyzing {seller_image_path.name} against {len(brand_images)} brand images...")
    print(f"Brand images: {[img.name for img in brand_images]}")
    
    try:
        # Prepare files dictionary for the request
        # FIXED: Open seller image first
        files = {}
        
        # Add seller image
        seller_file = open(seller_image_path, 'rb')
        files['seller_image'] = (seller_image_path.name, seller_file, 'image/jpeg')
        
        # FIXED: Add all brand images correctly
        brand_files = []
        for img_path in brand_images:
            brand_file = open(img_path, 'rb')
            brand_files.append((img_path.name, brand_file, 'image/jpeg'))
        
        # Add brand images to files (multiple files with same key)
        files['brand_images'] = brand_files
        
        print("📡 Making API request...")
        
        # FIXED: Correct way to send multiple files with same key
        files_for_request = [
            ('seller_image', (seller_image_path.name, open(seller_image_path, 'rb'), 'image/jpeg'))
        ]
        
        # Add each brand image separately
        for img_path in brand_images:
            files_for_request.append(
                ('brand_images', (img_path.name, open(img_path, 'rb'), 'image/jpeg'))
            )
        
        # Make the request
        response = requests.post(
            f"{PERCEPTUAL_AI_URL}/analyze/authenticity",
            files=files_for_request
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return
            
        result = response.json()
        print(f"🔍 Raw API Response: {result}")
        
        print("\n📊 Analysis Results:")
        print("==================")
        
        # FIXED: Parse the response correctly based on your API structure
        if result.get('status') == 'success' and 'result' in result:
            analysis = result['result']
            
            # Extract the main score (this is the final authenticity score)
            final_score = analysis.get('score', 0)
            match_found = analysis.get('match_found', False)
            closest_brand = analysis.get('closest_brand_image', 'Unknown')
            
            print(f"✅ Final Authenticity Score: {final_score:.3f}/1.000")
            print(f"🎯 Match Found: {'Yes' if match_found else 'No'}")
            print(f"🔗 Closest Brand Image: {closest_brand}")
            
            # Extract detailed scores
            details = analysis.get('details', {})
            print("\n🔍 Detailed Component Scores:")
            print(f"- Hash Match Score: {details.get('hash_match_score', 0):.3f}")
            print(f"- Semantic Similarity: {details.get('semantic_similarity', 0):.3f}")
            print(f"- Quality Score: {details.get('quality_score', 0):.3f}")
            
            print("\n🚨 Quality Analysis:")
            if details.get('is_blurry'):
                print("- ⚠️ Image appears blurry")
            else:
                print("- ✅ Image quality is acceptable")
                
            if details.get('is_tampered'):
                print("- ⚠️ Signs of image tampering detected")
            else:
                print("- ✅ No obvious tampering detected")
                
            if details.get('matches_brand'):
                print("- ✅ Product matches brand characteristics")
            else:
                print("- ⚠️ Product doesn't match brand images")
            
            # FIXED: Make determination based on the actual final score
            print(f"\n{'='*50}")
            if final_score < 0.3:
                print("❌ RESULT: HIGH RISK - This product appears to be COUNTERFEIT")
                print("   Recommendation: Block this listing immediately")
            elif final_score < 0.5:
                print("⚠️ RESULT: HIGH-MEDIUM RISK - This product is very suspicious")
                print("   Recommendation: Require additional verification")
            elif final_score < 0.7:
                print("🟡 RESULT: MEDIUM RISK - This product shows some suspicious signs")
                print("   Recommendation: Manual review recommended")
            elif final_score < 0.85:
                print("🟢 RESULT: LOW-MEDIUM RISK - Product appears mostly authentic")
                print("   Recommendation: Allow with monitoring")
            else:
                print("✅ RESULT: LOW RISK - This product appears to be AUTHENTIC")
                print("   Recommendation: Allow listing")
            print(f"{'='*50}")
            
        else:
            print("❌ Error: Unexpected response format")
            print(f"Response: {result}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {PERCEPTUAL_AI_URL}")
        print("   Make sure the Perceptual AI service is running on port 5003")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {str(e)}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close any open files
        try:
            for _, file_tuple in files_for_request:
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
        except:
            pass

def test_with_urls():
    """Alternative test using URLs instead of file uploads."""
    print("\n🌐 Testing with URLs (if you have online images)...")
    
    # Example URLs - replace with your actual test image URLs
    seller_image_url = "https://example.com/seller-product.jpg"
    brand_image_urls = [
        "https://example.com/brand-image-1.jpg",
        "https://example.com/brand-image-2.jpg"
    ]
    
    try:
        data = {
            "product_id": "test_product_123",
            "product_image_url": seller_image_url,
            "seller_id": "test_seller_456",
            "brand_image_urls": brand_image_urls
        }
        
        response = requests.post(f"{PERCEPTUAL_AI_URL}/analyze", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if 'authenticity_analysis' in result:
                analysis = result['authenticity_analysis']
                print(f"✅ URL-based Analysis Score: {analysis['score']:.3f}")
            else:
                print("⚠️ No authenticity analysis (brand images may be required)")
        else:
            print(f"❌ URL test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ URL test error: {str(e)}")

if __name__ == "__main__":
    test_fake_product_detection()
    # Uncomment the line below to test URL-based approach
    # test_with_urls()