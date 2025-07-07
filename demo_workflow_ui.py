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
from datetime import datetime
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
            
            # Let user select which image to use
            selected_image = st.selectbox(
                "Select a product image:",
                options=list(test_images.keys()),
                index=0  # Default to first image
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
            # Get the product image URL from the data ingestion results
            product_data = st.session_state.results.get("data_ingestion", {}).get("data", {})
            product_image_url = product_data.get("product_image_url")
            
            if not product_image_url:
                st.error("❌ No product image URL found in data ingestion results")
                st.stop()
                
            # Get brand images for comparison
            brand_images = get_test_images()
            brand_image_urls = [url for name, url in brand_images.items() if name.startswith('brand_')]
            
            analysis_request = {
                "product_id": st.session_state.product_id,
                "product_image_url": product_image_url,
                "brand_image_urls": brand_image_urls,  # Add brand images for comparison
                "metadata": {
                    "source": "demo_workflow",
                    "seller_id": product_data.get("seller_id", ""),
                    "product_name": product_data.get("product_name", "")
                }
            }
            try:
                response = requests.post(f"{SERVICES['perceptual_ai']}/analyze", json=analysis_request)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.results["perceptual_ai"] = result
                    
                    # Display the analysis results
                    st.success("✅ Image analysis complete!")
                    
                    # Show the hashes if available
                    if 'hashes' in result:
                        with st.expander("🔍 View Perceptual Hashes"):
                            st.json({"Perceptual Hashes": result['hashes']})
                    
                    # Show authenticity analysis if available
                    if 'authenticity_analysis' in result:
                        analysis = result['authenticity_analysis']
                        st.subheader("🔍 Authenticity Analysis")
                        
                        # Display score with visual indicator
                        score = analysis.get('score', 0)
                        st.metric("Authenticity Score", f"{score*100:.1f}%")
                        st.progress(score)
                        
                        # Display match status
                        if analysis.get('match_found'):
                            st.success("✅ This product matches known brand images")
                        else:
                            st.warning("⚠️ No close match found with brand images")
                            
                        # Show closest matching brand image if available
                        if analysis.get('closest_brand_image'):
                            st.image(analysis['closest_brand_image'], 
                                   caption=f"Closest matching brand image (Score: {score*100:.1f}%)",
                                   width=300)
                        
                        # Show detailed analysis in expander
                        with st.expander("📊 View Detailed Analysis"):
                            st.json(analysis.get('details', {}))
                    
                    elif 'brand_image_urls' in analysis_request and analysis_request['brand_image_urls']:
                        st.warning("⚠️ No brand images were available for authenticity comparison.")
                    
                    if st.button("Proceed to Review Analysis"):
                        st.session_state.demo_step = 3
                        st.rerun()
                else:
                    st.error(f"❌ Failed to analyze images: {response.status_code} - {response.text}")
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
                    "reviewer_id": "demo_user_1",  # Changed from user_id to reviewer_id
                    "rating": 5,
                    "text": "This product is amazing! Best purchase ever!",
                    "is_verified": True,  # Changed from is_verified_purchase to is_verified
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source": "demo_workflow"
                    }
                },
                {
                    "review_id": f"demo_review_{int(time.time())}_2",
                    "product_id": st.session_state.product_id,
                    "reviewer_id": "demo_user_2",  # Changed from user_id to reviewer_id
                    "rating": 1,
                    "text": "Terrible product, complete waste of money! This is clearly a fake product, not what was advertised at all. I'm very disappointed with this purchase.",
                    "is_verified": False,  # Changed from is_verified_purchase to is_verified
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "source": "demo_workflow"
                    }
                }
            ]
            st.session_state.review_ids = [r["review_id"] for r in test_reviews]
            review_results = []
            for review in test_reviews:
                try:
                    # Show which review is being analyzed
                    with st.expander(f"🔍 Analyzing review from {review['reviewer_id']}"):
                        st.write(f"**Rating:** {review['rating']}/5")
                        st.write(f"**Text:** {review['text']}")
                        
                        response = requests.post(f"{SERVICES['review_analyzer']}/analyze", json=review)
                        if response.status_code == 200:
                            result = response.json()
                            review_results.append(result)
                            
                            # Display analysis results
                            st.metric("Authenticity Score", f"{result.get('authenticity_score', 0) * 100:.1f}%")
                            st.progress(result.get('authenticity_score', 0))
                            
                            components = result.get('components', {})
                            if components:
                                st.write("**Analysis Components:**")
                                for comp, score in components.items():
                                    st.write(f"- {comp.replace('_', ' ').title()}: {score * 100:.1f}%")
                            
                            if result.get('is_suspicious', False):
                                st.warning("⚠️ This review was flagged as suspicious")
                            else:
                                st.success("✅ This review appears to be authentic")
                                
                        else:
                            st.error(f"❌ Failed to analyze review {review['review_id']}: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error connecting to Review Analyzer service for review {review['review_id']}: {str(e)}")
            if review_results:
                st.session_state.results["review_analyzer"] = review_results
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
                "seller_name": st.session_state.product_data.get("seller_name", "Demo Electronics Store"),
                "account_created_at": (datetime.utcnow() - timedelta(days=365)).isoformat(),
                "first_listing_date": (datetime.utcnow() - timedelta(days=180)).isoformat(),
                "total_orders": 245,
                "total_sales": 12500.0,
                "metadata": {
                    "source": "demo_workflow",
                    "trust_score": 0.87,
                    "response_rate": 0.95,
                    "response_time_hrs": 2.5
                },
                "products": [
                    {
                        "product_id": st.session_state.product_id,
                        "title": st.session_state.product_data.get("product_name", "High-End Wireless Earbuds"),
                        "description": "Premium noise-canceling wireless earbuds with 30-hour battery life and water resistance.",
                        "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat(),
                        "price": 159.99,
                        "category": "Electronics",
                        "is_high_risk": False
                    },
                    {
                        "product_id": f"{st.session_state.product_id}_2",
                        "title": "Wireless Charging Pad",
                        "description": "Fast wireless charging pad compatible with all Qi-enabled devices.",
                        "created_at": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                        "price": 29.99,
                        "category": "Electronics",
                        "is_high_risk": False
                    }
                ],
                "complaints": [
                    {
                        "complaint_id": f"comp_{int(time.time())}_1",
                        "type": "low",
                        "description": "Shipping was one day later than estimated",
                        "created_at": (datetime.utcnow() - timedelta(days=14)).isoformat(),
                        "result": "resolved"
                    },
                    {
                        "complaint_id": f"comp_{int(time.time())}_2",
                        "type": "medium",
                        "description": "Item description was slightly inaccurate",
                        "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                        "result": "refunded"
                    }
                ]
            }
            try:
                with st.expander("🔍 View Seller Data"):
                    st.json(seller_data)
                    
                response = requests.post(f"{SERVICES['seller_analyzer']}/analyze", json=seller_data)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.results["seller_analyzer"] = result
                    
                    # Display results in a user-friendly way
                    st.subheader("📊 Seller Analysis Results")
                    
                    # Create columns for metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Behavior Score", f"{result.get('behavior_score', 0) * 100:.1f}%")
                        st.progress(result.get('behavior_score', 0))
                    
                    with col2:
                        risk_level = result.get('risk_level', 'medium').capitalize()
                        st.metric("Risk Level", risk_level)
                        
                        # Color code the risk level
                        if risk_level.lower() == 'low':
                            st.success("✅ Low Risk")
                        elif risk_level.lower() == 'medium':
                            st.warning("⚠️ Medium Risk")
                        else:
                            st.error("❌ High Risk")
                    
                    with col3:
                        is_high_risk = result.get('is_high_risk', False)
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
                            st.write(f"**{component.replace('_', ' ').title()}:** {score*100:.1f}%")
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
                            trust_score = 1.0 - result["fraud_score"]
                            st.metric("Overall Trust Score", f"{trust_score * 100:.1f}%")
                            st.progress(trust_score)
                            
                            # Color code the trust score
                            if trust_score >= 0.7:
                                st.success("✅ High Trust")
                            elif trust_score >= 0.4:
                                st.warning("⚠️ Medium Trust")
                            else:
                                st.error("❌ Low Trust")
                    
                    with col2:
                        # Show agent information if available
                        if "agent_id" in result:
                            st.info(f"🤖 Analysis performed by: {result['agent_id']}")
                    
                    # Show detailed analysis in expandable sections
                    with st.expander("🔍 View Analysis Details", expanded=True):
                        st.subheader("Analysis Summary")
                        
                        # Display product information
                        if "product_info" in analysis_data:
                            with st.expander("📦 Product Information"):
                                st.json(analysis_data["product_info"])
                        
                        # Display perceptual analysis results
                        if "perceptual_analysis" in analysis_data and analysis_data["perceptual_analysis"]:
                            with st.expander("🖼️ Perceptual Analysis"):
                                st.json(analysis_data["perceptual_analysis"])
                        
                        # Display review analysis results
                        if "review_analysis" in analysis_data and analysis_data["review_analysis"]:
                            with st.expander("📝 Review Analysis"):
                                for i, review in enumerate(analysis_data["review_analysis"], 1):
                                    st.markdown(f"**Review {i}**")
                                    st.json(review)
                        
                        # Display seller analysis results
                        if "seller_analysis" in analysis_data and analysis_data["seller_analysis"]:
                            with st.expander("👤 Seller Analysis"):
                                st.json(analysis_data["seller_analysis"])
                    
                    # Display any additional metadata
                    if "metadata" in analysis_data:
                        with st.expander("📋 Analysis Metadata"):
                            st.json(analysis_data["metadata"])
                    
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
        trust_score = 1.0 - swarm_results.get("fraud_score", 0.3)  # Default to 70% trust if no score
        
        # Display the trust score prominently
        st.subheader("Trust Assessment")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Calculated Trust Score", f"{trust_score*100:.1f}%")
            st.progress(trust_score)
            
            # Color code the trust score
            if trust_score >= 0.7:
                st.success("✅ High Trust")
            elif trust_score >= 0.4:
                st.warning("⚠️ Medium Trust")
            else:
                st.error("❌ Low Trust")
        
        with col2:
            st.info("🔍 This score is based on:")
            st.markdown("• Perceptual AI Analysis")
            st.markdown("• Review Analysis")
            st.markdown("• Seller Behavior Analysis")
        
        st.markdown("---")
        
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
                    
                    # Prepare the trust event data
                    trust_event = {
                        "product_id": st.session_state.product_id,
                        "seller_id": st.session_state.seller_id,
                        "trust_score": trust_score,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "source": "demo_workflow",
                            "analysis_type": "full_workflow"
                        }
                    }
                    
                    # Since the ledger is append-only, we'll just show the current state
                    st.session_state.results["trust_ledger"] = {
                        "product_id": st.session_state.product_id,
                        "trust_score": trust_score,
                        "blockchain_length": initial_ledger_length,
                        "latest_block": ledger_data[-1] if ledger_data else None
                    }
                    
                    # Display the latest block
                    with st.expander("🔍 View Latest Block in Ledger", expanded=True):
                        if ledger_data:
                            latest_block = ledger_data[-1]
                            st.json(latest_block)
                            
                            # Show block details in a more readable format
                            if "data" in latest_block:
                                st.markdown("### Block Data")
                                st.json(latest_block["data"])
                                
                            if "timestamp" in latest_block:
                                timestamp = datetime.fromisoformat(latest_block["timestamp"].replace('Z', '+00:00'))
                                st.caption(f"Block Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                                
                            if "hash" in latest_block:
                                st.code(f"Block Hash: {latest_block['hash']}")
                        else:
                            st.info("No blocks in the ledger yet.")
                    
                    st.success("✅ Trust assessment ready to be recorded in the ledger")
                    
                    # Show a visual representation of the blockchain
                    if len(ledger_data) > 0:
                        with st.expander("⛓️ View Blockchain Visualization"):
                            st.markdown("### Blockchain Visualization")
                            for i, block in enumerate(ledger_data[-5:]):  # Show last 5 blocks
                                block_id = block.get("index", i)
                                block_hash = block.get("hash", "")[:8] + "..." if "hash" in block else ""
                                
                                # Create a visual block
                                block_color = "#4CAF50" if i == len(ledger_data) - 1 else "#2196F3"
                                st.markdown(
                                    f"""
                                    <div style='background-color: {block_color}; color: white; 
                                    padding: 10px; margin: 5px 0; border-radius: 5px;'>
                                    <strong>Block {block_id}</strong>: {block_hash}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                                
                                # Show arrow between blocks (except for the last one)
                                if i < len(ledger_data[-5:]) - 1:
                                    st.markdown("<div style='text-align: center;'>↓</div>", unsafe_allow_html=True)
                            
                            if st.button("✅ View Final Results"):
                                st.session_state.demo_step = 7
                                st.rerun()
                    else:
                        st.error(f"❌ Failed to record trust event: {response.status_code} - {response.text}")
                else:
                    st.error(f"❌ Failed to fetch ledger: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error connecting to Trust Ledger service: {str(e)}")
    else:
        st.error("Trust Ledger service is not available. Please check the service status in the sidebar.")

elif st.session_state.demo_step == 7:
    st.subheader("Final Results: TrustViz Workflow Demonstration")
    st.markdown("Here are the consolidated results from all steps of the TrustViz workflow.")
    
    with st.expander("Data Ingestion Results", expanded=True):
        st.json(st.session_state.results.get("data_ingestion", {}))
    
    with st.expander("Perceptual AI Analysis Results", expanded=True):
        st.json(st.session_state.results.get("perceptual_ai", {}))
    
    with st.expander("Review Analysis Results", expanded=True):
        st.json(st.session_state.results.get("review_analyzer", []))
    
    with st.expander("Seller Behavior Analysis Results", expanded=True):
        st.json(st.session_state.results.get("seller_analyzer", {}))
    
    with st.expander("Swarm Intelligence Results", expanded=True):
        st.json(st.session_state.results.get("swarm_intelligence", {}))
    
    with st.expander("Trust Ledger Final Trust Score", expanded=True):
        st.json(st.session_state.results.get("trust_ledger", {}))
    
    st.balloons()
    st.markdown("🎉 **Demo Complete!** Use the sidebar to reset and start a new demo.")
 