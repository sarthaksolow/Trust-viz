import requests
import json
from pprint import pprint

# Test configuration
PERCEPTUAL_AI_URL = "http://localhost:5003"  # Perceptual AI service runs on port 5003

def test_fake_product_detection():
    """Test the fake product detection with the provided clothing example."""
    print("🚀 Testing Fake Product Detection System")
    print("====================================")
    
    # Test data with the provided images
    test_data = {
        "product_id": "test_fake_abibas_001",
        "product_name": "Suspicious Abibas T-Shirt",
        "product_image_url": "https://images.squarespace-cdn.com/content/v1/5ab94f5e3c3a536987d16ce5/1553621431674-2EQGHV5O5Y0PET3L86CJ/abibas-TFE.jpg",
        "brand_image_urls": [
            "https://brand.assets.adidas.com/image/upload/f_auto,q_auto,fl_lossy/enUS/Images/Originals-SS22-Creators-OWD-September-Superstar-Shoes-ECOM-TM_Global_tcm221-920850.jpg",
            "https://assets.adidas.com/images/w_600,f_auto,q_auto/7c5d7a2a5f5d4a52af99af9b00d9f2c4_9366/Adicolor_Classics_Trefoil_Tee_Black_GN3158_01_laydown.jpg"
        ],
        "category": "clothing"
    }
    
    print("🔍 Analyzing product image against brand images...")
    try:
        # First, let's check the image authenticity
        # Download the seller image
        seller_img_response = requests.get(test_data['product_image_url'])
        seller_img_response.raise_for_status()
        
        # Prepare files dictionary for the request
        files = {
            'seller_image': ('seller.jpg', seller_img_response.content, 'image/jpeg')
        }
        
        # Download and add brand images
        for i, url in enumerate(test_data['brand_image_urls']):
            try:
                brand_img_response = requests.get(url)
                brand_img_response.raise_for_status()
                files[f'brand_images'] = (f'brand_{i}.jpg', brand_img_response.content, 'image/jpeg')
            except Exception as e:
                print(f"⚠️ Could not download brand image {url}: {str(e)}")
        
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

if __name__ == "__main__":
    test_fake_product_detection()
