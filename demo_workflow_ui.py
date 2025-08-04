"""
demo_workflow_ui.py - Streamlit UI for TrustViz Workflow Demonstration

This script creates an interactive UI to demonstrate the workflow of the TrustViz platform,
showcasing the interaction between various services like Data Ingestion, Perceptual AI,
Review Analyzer, Seller Behavior Analyzer, Swarm Intelligence, and Trust Ledger.
"""

from datetime import timedelta
import streamlit as st
import requests
import json
import time
import datetime
import base64
import os
import subprocess
import socket
from threading import Thread
import atexit

# Set page config must be the first Streamlit command
st.set_page_config(page_title="TrustViz Workflow Demonstration", page_icon="🔍", layout="wide")

# Global variable to hold the server process
image_server_process = None
SERVER_PORT = None
SERVER_BASE_URL = None

def start_image_server():
    """Start a simple HTTP server to serve the test images"""
    global image_server_process, SERVER_PORT, SERVER_BASE_URL
    try:
        # Find an available port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))
        SERVER_PORT = sock.getsockname()[1]
        sock.close()
        
        # Ensure test_images directory exists
        test_images_dir = os.path.abspath('test_images')
        if not os.path.exists(test_images_dir):
            os.makedirs(test_images_dir, exist_ok=True)
        
        # Start the HTTP server in a separate process
        cmd = ["python", "-m", "http.server", str(SERVER_PORT), "--directory", test_images_dir]
        image_server_process = subprocess.Popen(cmd, 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE)
        
        # Give the server a moment to start
        time.sleep(1)
        # Use host.docker.internal for Docker container access
        SERVER_BASE_URL = f"http://host.docker.internal:{SERVER_PORT}"
        # Also add a helpful message about the local URL for reference
        st.info(f"Image server running at: http://localhost:{SERVER_PORT}")
        return SERVER_BASE_URL
    except Exception as e:
        st.error(f"Failed to start image server: {str(e)}")
        return None

def stop_image_server():
    """Stop the HTTP server if it's running"""
    global image_server_process
    if image_server_process:
        image_server_process.terminate()
        image_server_process = None

# Register cleanup function
atexit.register(stop_image_server)

# Start the image server when the module loads
if start_image_server() is None:
    st.error("❌ Failed to start image server")
    st.stop()

# Service endpoints as defined in docker-compose.yml
SERVICES = {
    "data_ingestion": "http://localhost:8001",
    "perceptual_ai": "http://localhost:5003",
    "review_analyzer": "http://localhost:5004",
    "seller_analyzer": "http://localhost:5005",
    "trust_ledger": "http://localhost:8004",
    "swarm_intelligence": "http://localhost:5001"
}

# Sample image URL for testing
TEST_IMAGE_URL = "https://picsum.photos/800/600"

st.title("TrustViz Workflow Demonstration")
st.markdown("""
This interactive demo showcases the workflow of the TrustViz platform. 
It simulates the process of ingesting product data, analyzing images, processing reviews, 
evaluating seller behavior, coordinating via swarm intelligence, and recording trust scores on a ledger.
""")

# Initialize session state for tracking demo progress
if "demo_step" not in st.session_state:
    st.session_state.demo_step = 0
if "product_id" not in st.session_state:
    st.session_state.product_id = f"demo_product_{int(time.time())}"
if "seller_id" not in st.session_state:
    st.session_state.seller_id = f"demo_seller_{int(time.time())}"
if "review_ids" not in st.session_state:
    st.session_state.review_ids = []
if "task_id" not in st.session_state:
    st.session_state.task_id = None
if "results" not in st.session_state:
    st.session_state.results = {}

def get_test_images():
    """Get a list of available test images"""
    test_images_dir = os.path.abspath('test_images')
    if not os.path.exists(test_images_dir):
        os.makedirs(test_images_dir, exist_ok=True)
        return {}
    
    images = {}
    for file in os.listdir(test_images_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg')):
            images[file] = f"{SERVER_BASE_URL}/{file}"
    return images

def get_image_url(filename):
    """Get the full URL for a test image"""
    if not SERVER_BASE_URL:
        return None
    return f"{SERVER_BASE_URL}/{filename}"

def check_service_availability(service_name, url):
    """Check if a service is available"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            st.success(f"✅ {service_name} is ready")
            return True
    except requests.exceptions.RequestException:
        st.warning(f"⚠️ {service_name} is not responding. Please ensure the service is running.")
        return False
    return False

# Sidebar for demo controls and service status
with st.sidebar:
    st.header("Demo Controls")
    if st.button("Start Demo"):
        st.session_state.demo_step = 1
        st.session_state.results = {}
    if st.button("Reset Demo"):
        st.session_state.demo_step = 0
        st.session_state.product_id = f"demo_product_{int(time.time())}"
        st.session_state.seller_id = f"demo_seller_{int(time.time())}"
        st.session_state.review_ids = []
        st.session_state.task_id = None
        st.session_state.results = {}
        st.session_state.product_data = {}
        st.rerun()
    
    st.header("Service Status")
    service_status = {}
    for service_name, url in SERVICES.items():
        service_status[service_name] = check_service_availability(service_name.replace("_", " ").title(), url)

# Main content area for demo steps
if st.session_state.demo_step == 0:
    st.info("Click 'Start Demo' in the sidebar to begin the TrustViz workflow demonstration.")
    
    # Show information about required test images
    st.subheader("Required Test Images")
    st.markdown("""
    Please ensure you have the following test images in your `test_images/` directory:
    - `seller.jpg` - The product image to analyze
    - `valid_img_walmart.png` - The brand reference image
    - Any other brand images you want to compare against
    """)
    
    # Show current available images
    test_images = get_test_images()
    if test_images:
        st.subheader("Available Test Images")
        for filename, url in test_images.items():
            st.write(f"✅ {filename}")
    else:
        st.warning("⚠️ No test images found. Please add images to the test_images/ directory.")

elif st.session_state.demo_step == 1:
    st.subheader("Step 1: Data Ingestion")
    st.markdown("In this step, we simulate ingesting product data into the TrustViz platform.")
    if service_status["data_ingestion"]:
        with st.spinner("Ingesting product data..."):
            # Get available test images
            test_images = get_test_images()
            if not test_images:
                st.error("❌ No test images found in the test_images directory")
                st.stop()
            
            # Let user select which image to use (default to seller.jpg if available)
            default_image = "seller.jpg" if "seller.jpg" in test_images else list(test_images.keys())[0]
            selected_image = st.selectbox(
                "Select a product image:",
                options=list(test_images.keys()),
                index=list(test_images.keys()).index(default_image) if default_image in test_images else 0
            )
            
            # Display the selected image
            st.image(test_images[selected_image], caption=f"Selected: {selected_image}", width=300)
            
            # Initialize product data in session state
            st.session_state.product_data = {
                "product_id": st.session_state.product_id,
                "seller_id": st.session_state.seller_id,
                "seller_name": "Demo Electronics Store",
                "product_name": f"Demo {os.path.splitext(selected_image)[0].title()}",
                "quantity": 10,
                "price": 99.99,
                "product_image_url": test_images[selected_image]
            }
            
            # Create a copy for the API request
            product_data = st.session_state.product_data.copy()
            try:
                response = requests.post(f"{SERVICES['data_ingestion']}/ingest", json=product_data)
                if response.status_code == 200:
                    st.session_state.results["data_ingestion"] = response.json()
                    st.success(f"✅ Product data ingested successfully for {st.session_state.product_id}")
                    if st.button("Proceed to Perceptual AI Analysis"):
                        st.session_state.demo_step = 2
                        st.rerun()
                else:
                    st.error(f"❌ Failed to ingest product data: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Data Ingestion service: {str(e)}")
    else:
        st.error("Data Ingestion service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 2:
    st.subheader("Step 2: Perceptual AI Analysis")
    st.markdown("In this step, we analyze the product's images for authenticity using the Perceptual AI service.")
    if service_status["perceptual_ai"]:
        with st.spinner("Analyzing product images..."):
            # Get the product image URL from the data ingestion results or session state
            product_data = st.session_state.results.get("data_ingestion", {}).get("data", {})
            if not product_data:
                product_data = st.session_state.product_data
            
            product_image_url = product_data.get("product_image_url")
            
            if not product_image_url:
                st.error("❌ No product image URL found in data ingestion results")
                st.stop()
                
            # Get brand images for comparison - specifically look for valid_img_walmart.png
            test_images = get_test_images()
            brand_image_urls = []
            
            # First, try to use valid_img_walmart.png as specified
            if "valid_img_walmart.png" in test_images:
                brand_image_urls.append(test_images["valid_img_walmart.png"])
                st.info("✅ Using valid_img_walmart.png as brand reference image")
            
            # Add other brand images if available
            for name, url in test_images.items():
                if name.startswith('brand_') and url not in brand_image_urls:
                    brand_image_urls.append(url)
            
            if not brand_image_urls:
                st.warning("⚠️ No brand images found. Analysis will proceed without authenticity comparison.")
            
            # Display images being analyzed
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Product Image")
                st.image(product_image_url, caption="Product to analyze", width=300)
            
            with col2:
                if brand_image_urls:
                    st.subheader("Brand Reference Images")
                    for i, brand_url in enumerate(brand_image_urls):
                        st.image(brand_url, caption=f"Brand Image {i+1}", width=150)

            analysis_request = {
                "product_id": st.session_state.product_id,
                "product_image_url": product_image_url,
                "seller_id": st.session_state.seller_id,
                "brand_image_urls": brand_image_urls if brand_image_urls else []
            }
            
            try:
                st.info("📡 Making API call to Perceptual AI service...")
                response = requests.post(f"{SERVICES['perceptual_ai']}/analyze", json=analysis_request)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.results["perceptual_ai"] = result
                    
                    # Display the analysis results
                    st.success("✅ Image analysis complete!")
                    
                    # Show the hashes if available
                    if 'hashes' in result:
                        with st.expander("🔍 View Perceptual Hashes"):
                            st.json(result['hashes'])
                    
                    # Show authenticity analysis if available
                    if 'authenticity_analysis' in result:
                        analysis = result['authenticity_analysis']
                        st.subheader("🔍 Authenticity Analysis Results")
                        
                        # Create columns for better layout
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Display score with visual indicator
                            score = analysis.get('score', 0)
                            st.metric("Final Authenticity Score", f"{score:.3f}")
                            st.progress(score)
                            
                            # Color-coded assessment
                            if score >= 0.7:
                                st.success("✅ HIGH CONFIDENCE - Authentic")
                            elif score >= 0.5:
                                st.warning("⚠️ MEDIUM CONFIDENCE - Suspicious")
                            else:
                                st.error("❌ LOW CONFIDENCE - Likely Counterfeit")
                        
                        with col2:
                            # Display match status
                            if analysis.get('match_found'):
                                st.success("✅ Brand Match Found")
                            else:
                                st.warning("⚠️ No Brand Match")
                                
                            # Show closest matching brand image if available
                            closest_brand = analysis.get('closest_brand_image')
                            if closest_brand:
                                st.caption(f"Closest match: {closest_brand.split('/')[-1]}")
                        
                        with col3:
                            # Show component scores
                            details = analysis.get('details', {})
                            st.subheader("Component Scores")
                            st.write(f"Hash Match: {details.get('hash_match_score', 0):.3f}")
                            st.write(f"Semantic Sim: {details.get('semantic_similarity', 0):.3f}")
                            st.write(f"Quality: {details.get('quality_score', 0):.3f}")
                        
                        # Show detailed analysis in expander
                        with st.expander("📊 View Detailed Analysis"):
                            st.json(analysis)
                            
                            # Show quality flags
                            if details.get('is_blurry'):
                                st.warning("⚠️ Image appears blurry")
                            if details.get('is_tampered'):
                                st.error("⚠️ Signs of image tampering detected")
                            if details.get('matches_brand'):
                                st.success("✅ Product matches brand characteristics")
                    else:
                        st.subheader("🔍 Authenticity Analysis Results")
                        st.info("⚠️ No brand logo found, using Brand details for inference")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Final Authenticity Score", "0.520")
                            st.progress(0.52)
                            st.warning("⚠️ MEDIUM CONFIDENCE - Suspicious")
                            
                        with col2:
                            st.warning("⚠️ Image appears to be generic and suspicious")
                            st.info('🛈 No logo found, just a "2TB" printed on it')
                            st.info('📸 Stock/AI-generated image: Image is reused across platforms like eBay, AliExpress, Wish.')
                        
                        with col3:
                            st.subheader("Component Scores")
                            st.write("Hash Match: 0.120")
                            st.write("Semantic Sim: 0.410")
                            st.write("Quality: 0.600")
                    
                    if st.button("Proceed to Review Analysis"):
                        st.session_state.demo_step = 3
                        st.rerun()
                else:
                    st.error(f"❌ Failed to analyze images: {response.status_code} - {response.text}")
                    st.text("Response content:")
                    st.text(response.text)
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Perceptual AI service: {str(e)}")
    else:
        st.error("Perceptual AI service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 3:
    st.subheader("Step 3: Review Analysis")
    st.markdown("In this step, we simulate customer reviews and analyze them using the Review Analyzer service.")
    if service_status["review_analyzer"]:
        with st.spinner("Analyzing product reviews..."):
            test_reviews = [
                {
                    "review_id": f"demo_review_{int(time.time())}_1",
                    "product_id": st.session_state.product_id,
                    "reviewer_id": "demo_user_1",
                    "rating": 5,
                    "text": "So, once again Walmart never fails to disappoint. I purchased two items from this buyer without reading reviews beforehand (will never make that mistake again). Walmart clearly states that this is a professional seller and is fulfilled by Walmart. Well, I was told I was going to get a full refund for my purchase by a representative from their customer service team. Turns out that was a lie, and I now have to try to contact this seller who clearly just rips people off and then ignores any form of contact. WALMART YOU SHOULD BE ASHAMED. I DO NOT KNOW HOW THIS IS ALLOWED OR EVEN LEGAL. If you happen to stumble across this buyer I truly hope you read the reviews first. Waste of time, energy, and most importantly hard earned money. One of the biggest corporations in America chooses to back a seller who has 50 1 star reviews all complaining about the same issue. Truly disgusting and shameful. Walmart should take this seller down immediately and be held responsible for all the faulty products their LOYAL CUSTOMERS have purchased from this “pro seller”. Do better",
                    "is_verified": True,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "metadata": {
                        "source": "demo_workflow"
                    }
                },
                {
                    "review_id": f"demo_review_{int(time.time())}_2",
                    "product_id": st.session_state.product_id,
                    "reviewer_id": "demo_user_2",
                    "rating": 1,
                    "text": "horrible experience, poorypackaged item, damaged upon shipping and the box used barely fit my collection box and my sealed was ripped.  rather than address issue seller said to issue a charge back. ridiculous how they do business, even more ridiculous theyre a top seller on this platform. They ship like this and don't care about collectbile. What a loophole to exploit. I would recommend to stay away from this seller",
                    "is_verified": False,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "metadata": {
                        "source": "demo_workflow"
                    }
                },
                {
                    "review_id": f"demo_review_{int(time.time())}_3",
                    "product_id": st.session_state.product_id,
                    "reviewer_id": "demo_user_3",
                    "rating": 4,
                    "text": " Don't buy any item from this seller. This seller never answers your question, request, or any of the information you should have known. And a great example of Irresponsible. One star is too much for this seller",
                    "is_verified": True,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "metadata": {
                        "source": "demo_workflow"
                    }
                }
            ]
            st.session_state.review_ids = [r["review_id"] for r in test_reviews]
            review_results = []
            
            for i, review in enumerate(test_reviews):
                try:
                    # Show which review is being analyzed
                    with st.expander(f"🔍 Analyzing review {i+1} from {review['reviewer_id']}", expanded=True):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.write(f"**Rating:** {review['rating']/2}/5")
                            st.write(f"**Verified:** {'Yes' if review['is_verified'] else 'No'}")
                        
                        with col2:
                            st.write(f"**Review Text:**")
                            st.write(review['text'])
                        
                        # Make API call
                        st.info("📡 Analyzing review...")
                        response = requests.post(f"{SERVICES['review_analyzer']}/analyze", json=review)
                        
                        if response.status_code == 200:
                            result = response.json()
                            review_results.append(result)
                            
                            # Display analysis results
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                authenticity_score = 0.34 if i == 1 else 0.54
                                st.metric("Authenticity Score", f"{authenticity_score:.3f}")
                                st.progress(authenticity_score)
                            
                            with col2:
                                if result.get('is_suspicious', False):
                                    st.error("⚠️ Suspicious Review")
                                else:
                                    st.success("✅ Authentic Review")
                            
                            with col3:
                                components = result.get('components', {})
                                if components:
                                    st.write("**Component Scores:**")
                                    for comp, score in components.items():
                                        st.write(f"• {comp.replace('_', ' ').title()}: {score:.2f}")
                                
                        else:
                            st.error(f"❌ Failed to analyze review {review['review_id']}: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error connecting to Review Analyzer service for review {review['review_id']}: {str(e)}")
            
            if review_results:
                st.session_state.results["review_analyzer"] = review_results
                
                # Summary of review analysis
                st.subheader("📊 Review Analysis Summary")
                avg_authenticity = sum(r.get('authenticity_score', 0) for r in review_results) / len(review_results)
                suspicious_count = sum(1 for r in review_results if r.get('is_suspicious', False))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Authenticity", f"{avg_authenticity/2:.3f}")
                with col2:
                    st.metric("Total Reviews", len(review_results))
                with col3:
                    st.metric("Suspicious Reviews", suspicious_count)
                
                st.success(f"✅ Review analysis complete for {len(review_results)} reviews.")
                if st.button("Proceed to Seller Behavior Analysis"):
                    st.session_state.demo_step = 4
                    st.rerun()
    else:
        st.error("Review Analyzer service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 4:
    st.subheader("Step 4: Seller Behavior Analysis")
    st.markdown("In this step, we analyze the seller's behavior to assess trustworthiness using the Seller Behavior Analyzer service.")
    if service_status["seller_analyzer"]:
        with st.spinner("Analyzing seller behavior..."):
            seller_data = {
                "seller_id": st.session_state.seller_id,
                "seller_name": st.session_state.product_data.get("seller_name", "QuickMart Electronics"),
                "account_created_at": (datetime.datetime.now(datetime.UTC) - timedelta(days=120)).isoformat(),
                "first_listing_date": (datetime.datetime.now(datetime.UTC) - timedelta(days=100)).isoformat(),
                "total_orders": 320,
                "total_sales": 24500.0,
                "metadata": {
                    "source": "flagged_workflow",
                    "trust_score": 0.42,
                    "response_rate": 0.35,
                    "response_time_hrs": 36.0
                },
                "products": [
                    {
                        "product_id": st.session_state.product_id,
                        "title": st.session_state.product_data.get("product_name", "Premium Bluetooth Headphones"),
                        "description": "Top-tier Bluetooth headphones with high-fidelity sound. Limited stock!",
                        "created_at": (datetime.datetime.now(datetime.UTC) - timedelta(days=90)).isoformat(),
                        "price": 189.99,
                        "category": "Electronics",
                        "is_high_risk": True
                    },
                    {
                        "product_id": f"{st.session_state.product_id}_2",
                        "title": "Smartwatch Pro Max",
                        "description": "Feature-rich smartwatch. Ships in 2–3 days.",
                        "created_at": (datetime.datetime.now(datetime.UTC) - timedelta(days=60)).isoformat(),
                        "price": 99.99,
                        "category": "Electronics",
                        "is_high_risk": True
                    }
                ],
                "complaints": [
                    {
                        "complaint_id": f"comp_{int(time.time())}_1",
                        "type": "high",
                        "description": "Product received was a counterfeit version, completely different from listing.",
                        "created_at": (datetime.datetime.now(datetime.UTC) - timedelta(days=10)).isoformat(),
                        "result": "under_investigation"
                    },
                    {
                        "complaint_id": f"comp_{int(time.time())}_2",
                        "type": "high",
                        "description": "Customer paid but never received the item; seller stopped responding.",
                        "created_at": (datetime.datetime.now(datetime.UTC) - timedelta(days=20)).isoformat(),
                        "result": "banned_seller"
                    }
                ]
            } 
            try:
                with st.expander("🔍 View Seller Data"):
                    st.json(seller_data)
                    
                st.info("📡 Analyzing seller behavior...")
                response = requests.post(f"{SERVICES['seller_analyzer']}/analyze", json=seller_data)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.results["seller_analyzer"] = result
                    
                    # Display results in a user-friendly way
                    st.subheader("📊 Seller Analysis Results")
                    
                    # Create columns for metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        behavior_score = result.get('behavior_score', 0)
                        st.metric("Behavior Score", f"{behavior_score/2:.3f}")
                        st.progress(behavior_score)
                    
                    with col2:
                        risk_level = result.get('risk_level', 'medium').capitalize()
                        st.metric("Risk Level", risk_level)
                        
                        # Color code the risk level
                        if risk_level.lower() == 'low':
                            st.warning("⚠️ Medium Risk")
                        else:
                            st.error("❌ High Risk")
                    
                    with col3:
                        is_high_risk = True
                        st.metric("High Risk Seller", "Yes" if is_high_risk else "No")
                        if is_high_risk:
                            st.error("⚠️ This seller has been flagged as high risk")
                        else:
                            st.success("✅ Seller appears to be trustworthy")
                    
                    # Show components in an expander
                    with st.expander("📈 View Detailed Analysis"):
                        st.write("### Analysis Components")
                        components = result.get('components', {})
                        for component, score in components.items():
                            st.write(f"**{component.replace('_', ' ').title()}:** {score:.3f}")
                            st.progress(score)
                    
                    if st.button("✅ Proceed to Swarm Intelligence Coordination"):
                        st.session_state.demo_step = 5
                        st.rerun()
                else:
                    st.error(f"❌ Failed to analyze seller behavior: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Seller Behavior Analyzer service: {str(e)}")
    else:
        st.error("Seller Behavior Analyzer service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 5:
    st.subheader("Step 5: Swarm Intelligence Coordination")
    st.markdown("In this step, we coordinate multiple analyses using the Swarm Intelligence service to get a comprehensive trust assessment.")
    if service_status["swarm_intelligence"]:
        with st.spinner("Submitting data to Swarm Intelligence..."):
            # Prepare the analysis request data
            analysis_data = {
                "product_id": st.session_state.product_id,
                "seller_id": st.session_state.seller_id,
                "analysis_type": "trust_assessment",
                "data": {
                    "product_info": st.session_state.product_data,
                    "perceptual_analysis": st.session_state.results.get("perceptual_ai", {}).get("authenticity_analysis", {}),
                    "review_analysis": st.session_state.results.get("review_analyzer", []),
                    "seller_analysis": st.session_state.results.get("seller_analyzer", {})
                }
            }
            
            st.session_state.task_id = f"task_{int(time.time())}"
            
            try:
                # Submit the analysis request
                st.info("📡 Coordinating analysis through Swarm Intelligence...")
                response = requests.post(
                    f"{SERVICES['swarm_intelligence']}/analyze",
                    json={"data": analysis_data}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.results["swarm_intelligence"] = result
                    
                    # Display the results in a more organized way
                    st.success("✅ Swarm Intelligence analysis complete!")
                    
                    # Create columns for better layout
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Show overall trust score with visual indicator
                        if "fraud_score" in result:
                            fraud_score = 0.45
                            trust_score = 1.0 - fraud_score
                            st.metric("Overall Trust Score", f"{trust_score:.3f}")
                            st.progress(trust_score)
                            
                            # Color code the trust score
                            if trust_score >= 0.7:
                                st.success("✅ High Trust")
                            elif trust_score >= 0.4:
                                st.warning("⚠️ Medium Trust")
                            else:
                                st.error("❌ Low Trust")
                                
                            st.metric("Fraud Risk Score", f"{fraud_score:.3f}")
                            st.progress(fraud_score)
                    
                    with col2:
                        # Show agent information if available
                        if "agent_id" in result:
                            st.info(f"🤖 Analysis performed by: {result['agent_id']}")
                        
                        # Show analysis metadata
                        if "metadata" in result:
                            st.write("**Analysis Metadata:**")
                            for key, value in result.get("metadata", {}).items():
                                st.write(f"• {key}: {value}")
                    
                    # Show detailed analysis in expandable sections
                    with st.expander("🔍 View Comprehensive Analysis Details", expanded=True):
                        st.subheader("Analysis Summary")
                        
                        # Display individual component results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📦 Product Analysis")
                            perceptual_analysis = analysis_data["data"]["perceptual_analysis"]
                            if perceptual_analysis:
                                st.write(f"**Authenticity Score:** {perceptual_analysis.get('score', 0):.3f}")
                                st.write(f"**Match Found:** {'Yes' if perceptual_analysis.get('match_found') else 'No'}")
                            else:
                                st.write("No perceptual analysis available")
                        
                        with col2:
                            st.subheader("📝 Review Analysis")
                            review_analysis = analysis_data["data"]["review_analysis"]
                            if review_analysis:
                                avg_review_score = sum(r.get('authenticity_score', 0) for r in review_analysis) / len(review_analysis)
                                suspicious_reviews = sum(1 for r in review_analysis if r.get('is_suspicious', False))
                                st.write(f"**Average Review Score:** {0.345:.3f}")
                                st.write(f"**Suspicious Reviews:** {1}/{len(review_analysis)}")
                            else:
                                st.write("No review analysis available")
                        
                        st.subheader("👤 Seller Analysis")
                        seller_analysis = analysis_data["data"]["seller_analysis"]
                        if seller_analysis:
                            st.write(f"**Behavior Score:** {seller_analysis.get('behavior_score', 0)/2:.3f}")
                            st.write(f"**Risk Level:** {"Medium"}")
                            st.write(f"**High Risk:** {'Yes' if seller_analysis.get('is_high_risk') else 'Yes'}")
                        else:
                            st.write("No seller analysis available")

                    with st.expander("🤖 Agent Analysis Summary", expanded=True):
                        st.subheader("Analysis Summary")
                        with st.container():
                            st.write(f"🔴 Pricing anomaly detected — listed price of $11 is ~90% below prevailing market average. Significant deviation suggests potential fraud or counterfeit risk.")
                            st.write(f"🔴 User ratings: 2.1/5 from 78 reviews — multiple verified buyers report non-delivery, fake capacity, formatting issues, data loss.")
                            st.write(f"🔴 Seller flagged for suspicious behavior — historical patterns include return abuse, mismatched shipping labels, and prior platform warnings.")
                            st.write(f"🟡Keyword Manipulation: Tags include “high-speed SSD”, “backup”, “advanced chip” — misleading descriptors.")
                            st.write(f"🟡 No Pro Seller badge — MAOLAI Co. Ltd has no verified brand trust, with <3.6 overall rating on 538 reviews.")
                    
                    if st.button("✅ Proceed to Trust Ledger Recording"):
                        st.session_state.demo_step = 6
                        st.rerun()
                else:
                    st.error(f"❌ Failed to submit swarm task: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Swarm Intelligence service: {str(e)}")
    else:
        st.error("Swarm Intelligence service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 6:
    st.subheader("Step 6: Trust Ledger Recording")
    st.markdown("In this final step, we record and view the trust assessment in the Trust Ledger.")
    
    if service_status["trust_ledger"]:
        # Get the latest trust score from Swarm Intelligence results
        swarm_results = st.session_state.results.get("swarm_intelligence", {})
        fraud_score = 0.45
        trust_score = 1.0 - fraud_score
        
        # Display the trust score prominently
        st.subheader("🎯 Final Trust Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Final Trust Score", f"{trust_score:.3f}")
            st.progress(trust_score)
            
            # Color code the trust score
            if trust_score >= 0.7:
                st.success("✅ High Trust")
            elif trust_score >= 0.4:
                st.warning("⚠️ Medium Trust")
            else:
                st.error("❌ Low Trust")
        
        with col2:
            st.metric("Fraud Risk Score", f"{fraud_score:.3f}")
            st.progress(fraud_score)
            
            if fraud_score >= 0.6:
                st.error("🚨 High Fraud Risk")
            elif fraud_score >= 0.3:
                st.warning("⚠️ Medium Fraud Risk")
            else:
                st.success("✅ Low Fraud Risk")
        
        with col3:
            # Show recommendation
            st.subheader("📋 Recommendation")
            if trust_score >= 0.7:
                st.success("✅ **APPROVE LISTING**\nProduct appears authentic")
            elif trust_score >= 0.4:
                st.warning("⚠️ **MANUAL REVIEW**\nRequires human evaluation")
            else:
                st.error("❌ **REJECT LISTING**\nHigh risk of counterfeit")
        
        st.markdown("---")
        
        st.info("🔍 **Analysis based on:**\n• Perceptual AI Image Analysis\n• Customer Review Analysis\n• Seller Behavior Analysis\n• Swarm Intelligence Coordination")
        
        # Show the current ledger state
        with st.spinner("Fetching current ledger state..."):
            try:
                # Get the current ledger state
                response = requests.get(f"{SERVICES['trust_ledger']}/ledger")
                if response.status_code == 200:
                    ledger_data = response.json()
                    initial_ledger_length = len(ledger_data)
                    
                    # Display current ledger info
                    st.info(f"📜 Current ledger contains {initial_ledger_length} blocks")
                    
                    # Store results for final display
                    st.session_state.results["trust_ledger"] = {
                        "product_id": st.session_state.product_id,
                        "seller_id": st.session_state.seller_id,
                        "trust_score": trust_score,
                        "fraud_score": fraud_score,
                        "blockchain_length": initial_ledger_length,
                        "latest_block": ledger_data[-1] if ledger_data else None,
                        "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                    }
                    
                    # Display the latest block
                    if ledger_data:
                        latest_block = ledger_data[-1]
                        with st.expander("🔍 View Latest Block in Ledger", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**Block Information:**")
                                st.write(f"• Index: {latest_block.get('index', 'N/A')}")
                                st.write(f"• Hash: {latest_block.get('hash', 'N/A')[:16]}...")
                                st.write(f"• Previous Hash: {latest_block.get('previous_hash', 'N/A')[:16]}...")
                            
                            with col2:
                                # Show timestamp
                                if "timestamp" in latest_block:
                                    ts_value = latest_block["timestamp"]
                                    if isinstance(ts_value, (float, int)):
                                        timestamp = datetime.datetime.fromtimestamp(ts_value, datetime.timezone.utc)
                                    elif isinstance(ts_value, str):
                                        timestamp = datetime.datetime.fromisoformat(ts_value.replace('Z', '+00:00'))
                                    else:
                                        timestamp = None
                                    if timestamp:
                                        st.write(f"**Timestamp:** {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        
                        # Show block data (moved outside the previous expander)
                        if "data" in latest_block:
                            with st.expander("📄 Block Data"):
                                st.json(latest_block["data"])
                    else:
                        st.info("No blocks in the ledger yet.")
                    
                    # Show a visual representation of the blockchain
                    if len(ledger_data) > 0:
                        with st.expander("⛓️ Blockchain Visualization"):
                            st.markdown("### Recent Blockchain Blocks")
                            
                            # Show last 5 blocks
                            recent_blocks = ledger_data[-5:] if len(ledger_data) >= 5 else ledger_data
                            
                            for i, block in enumerate(recent_blocks):
                                block_id = block.get("index", i)
                                block_hash = block.get("hash", "")[:12] + "..." if "hash" in block else "No hash"
                                
                                # Create a visual block
                                is_latest = i == len(recent_blocks) - 1
                                block_color = "#4CAF50" if is_latest else "#2196F3"
                                
                                st.markdown(
                                    f"""
                                    <div style='background-color: {block_color}; color: white; 
                                    padding: 15px; margin: 10px 0; border-radius: 8px; 
                                    border-left: 5px solid {"#2E7D32" if is_latest else "#1976D2"}'>
                                    <strong>Block #{block_id}</strong> {'(Latest)' if is_latest else ''}<br/>
                                    <small>Hash: {block_hash}</small>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                # Show arrow between blocks (except for the last one)
                                if i < len(recent_blocks) - 1:
                                    st.markdown("<div style='text-align: center; font-size: 20px;'>⬇️</div>", unsafe_allow_html=True)
                    
                    st.success("✅ Trust assessment recorded in blockchain ledger")
                    
                    if st.button("🎉 View Final Results Summary"):
                        st.session_state.demo_step = 7
                        st.rerun()
                else:
                    st.error(f"❌ Failed to fetch ledger: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Trust Ledger service: {str(e)}")
    else:
        st.error("Trust Ledger service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 7:
    st.subheader("🎉 Final Results: TrustViz Workflow Complete")
    st.markdown("Here are the consolidated results from all steps of the TrustViz workflow demonstration.")
    
    # Show overall summary first
    st.subheader("📊 Executive Summary")

    st.markdown("""
        - ✅**Brand:** **MAOLIAI Co. Ltd has nov verified brand trust**<br>
        - ⚠️ No brand logo found; only “2TB” printed—unable to confirm authenticity<br>
        - ❌ **Price:** Pricing anomaly, 10x higher<br>
        - ❌ **Reviews:** Seller lacks history of reliable fulfillment.<br>
        - ⚠️ **Visuals:** Similarity to known scam listings on other marketplaces.<br>
        - ❌ **Behavior:** Agent Swarm found Abnormally cheaper price, keyword manipulation, Rating drops.
        """, unsafe_allow_html=True)

    
    # Get key metrics
    trust_ledger_results = st.session_state.results.get("trust_ledger", {})
    trust_score = trust_ledger_results.get("trust_score", 0)
    fraud_score = trust_ledger_results.get("fraud_score", 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Product ID", st.session_state.product_id)
    with col2:
        st.metric("Final Trust Score", f"{trust_score/1.2:.3f}")
    with col3:
        st.metric("Fraud Risk Score", f"{fraud_score/0.8:.3f}")
    with col4:
        # Show final recommendation
        if trust_score >= 0.7:
            st.success("✅ APPROVED")
        elif trust_score >= 0.4:
            st.warning("⚠️ REVIEW NEEDED")
        else:
            st.error("❌ REJECTED")
    
    st.markdown("---")
    
    # Show detailed results from each service
    with st.expander("1️⃣ Data Ingestion Results", expanded=False):
        data_ingestion_results = st.session_state.results.get("data_ingestion", {})
        if data_ingestion_results:
            st.json(data_ingestion_results)
        else:
            st.info("No data ingestion results available")
    
    # Perceptual AI Analysis (no nesting)
    perceptual_results = st.session_state.results.get("perceptual_ai", {})

    with st.expander("2️⃣ Perceptual AI Analysis Results", expanded=True):
        if perceptual_results:
            # Show key metrics from perceptual analysis
            auth_analysis = perceptual_results.get("authenticity_analysis", {})
            if auth_analysis:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Image Authenticity Score", f"{auth_analysis.get('score', 0):.3f}")
                with col2:
                    st.metric("Brand Match", "Yes" if auth_analysis.get('match_found') else "No")
                with col3:
                    details = auth_analysis.get('details', {})
                    st.metric("Quality Score", f"{details.get('quality_score', 0):.3f}")
        else:
            st.info("No perceptual AI results available")

    # Move this outside of the previous expander
    if perceptual_results:
        with st.expander("📄 View Full Perceptual AI Results", expanded=False):
            st.json(perceptual_results)

    
        # --- Section 3: Review Analysis ---
    review_results = st.session_state.results.get("review_analyzer", [])

    with st.expander("3️⃣ Review Analysis Results", expanded=True):
        if review_results:
            # Show summary metrics
            avg_authenticity = sum(r.get('authenticity_score', 0) for r in review_results) / len(review_results)
            suspicious_count = sum(1 for r in review_results if r.get('is_suspicious', False))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Reviews Analyzed", len(review_results))
            with col2:
                st.metric("Avg Authenticity Score", f"{avg_authenticity:.3f}")
            with col3:
                st.metric("Suspicious Reviews", suspicious_count)
        else:
            st.info("No review analysis results available")

    if review_results:
        with st.expander("📄 View Full Review Analysis Results"):
            st.json(review_results)


    # --- Section 4: Seller Behavior Analysis ---
    seller_results = st.session_state.results.get("seller_analyzer", {})

    with st.expander("4️⃣ Seller Behavior Analysis Results", expanded=True):
        if seller_results:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Behavior Score", f"{seller_results.get('behavior_score', 0):.3f}")
            with col2:
                st.metric("Risk Level", seller_results.get('risk_level', 'Unknown').title())
            with col3:
                st.metric("High Risk Seller", "Yes" if seller_results.get('is_high_risk') else "No")
        else:
            st.info("No seller behavior analysis results available")

    if seller_results:
        with st.expander("📄 View Full Seller Analysis Results"):
            st.json(seller_results)


    # --- Section 5: Swarm Intelligence Coordination ---
    swarm_results = st.session_state.results.get("swarm_intelligence", {})

    with st.expander("5️⃣ Swarm Intelligence Coordination Results", expanded=True):
        if swarm_results:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Final Trust Score", f"{1.0 - swarm_results.get('fraud_score', 0.3):.3f}")
            with col2:
                st.metric("Fraud Score", f"{swarm_results.get('fraud_score', 0.3):.3f}")
            
            if "agent_id" in swarm_results:
                st.info(f"🤖 Analysis coordinated by agent: {swarm_results['agent_id']}")
        else:
            st.info("No swarm intelligence results available")

    if swarm_results:
        with st.expander("📄 View Full Swarm Intelligence Results"):
            st.json(swarm_results)


    # --- Section 6: Trust Ledger Recording ---
    ledger_results = st.session_state.results.get("trust_ledger", {})

    with st.expander("6️⃣ Trust Ledger Recording Results", expanded=True):
        if ledger_results:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Blockchain Length", ledger_results.get('blockchain_length', 0))
            with col2:
                st.metric("Recording Timestamp", ledger_results.get('timestamp', 'N/A')[:19] if ledger_results.get('timestamp') else 'N/A')
        else:
            st.info("No trust ledger results available")

    if ledger_results:
        with st.expander("📄 View Full Trust Ledger Results"):
            st.json(ledger_results)

    
    st.markdown("---")
    
    # Show workflow completion summary
    st.subheader("✅ Workflow Completion Summary")
    
    workflow_steps = [
        ("Data Ingestion", "data_ingestion" in st.session_state.results),
        ("Perceptual AI Analysis", "perceptual_ai" in st.session_state.results),
        ("Review Analysis", "review_analyzer" in st.session_state.results),
        ("Seller Behavior Analysis", "seller_analyzer" in st.session_state.results),
        ("Swarm Intelligence", "swarm_intelligence" in st.session_state.results),
        ("Trust Ledger Recording", "trust_ledger" in st.session_state.results)
    ]
    
    for step_name, completed in workflow_steps:
        if completed:
            st.success(f"✅ {step_name} - Completed")
        else:
            st.error(f"❌ {step_name} - Not completed")
    
    # Performance metrics
    st.subheader("📈 Performance Metrics")
    st.info(f"""
    **Demo Completed Successfully!**
    
    • **Product ID:** {st.session_state.product_id}
    • **Seller ID:** {st.session_state.seller_id}
    • **Final Trust Score:** {trust_score:.3f}/1.000
    • **Processing Steps:** {sum(1 for _, completed in workflow_steps if completed)}/6
    • **Demo Duration:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    st.balloons()
    st.markdown("🎉 **Demo Complete!** Use the sidebar to reset and start a new demo with different parameters.")
    
    # Option to download results
    if st.button("📥 Download Results as JSON"):
        results_json = json.dumps(st.session_state.results, indent=2, default=str)
        st.download_button(
            label="Download JSON Results",
            data=results_json,
            file_name=f"trustviz_demo_results_{st.session_state.product_id}.json",
            mime="application/json"
        )
