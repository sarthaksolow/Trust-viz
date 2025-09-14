import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Fraud Detection Swarm Intelligence",
    page_icon="🕵️",
    layout="wide"
)

st.title("🕵️ Fraud Detection Swarm Intelligence Dashboard")
st.write("Multi-Agent CrewAI System for E-commerce Fraud Detection")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Manual Analysis", "Simulation", "System Health"])

# API endpoints
API_BASE = "http://localhost:5001"

def make_api_request(endpoint, method="GET", data=None):
    """Helper function to make API requests"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Make sure the FastAPI server is running on port 5001.")
        return None
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None

# Dashboard page
if page == "Dashboard":
    st.header("System Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("System Health")
        if st.button("Check Health"):
            health = make_api_request("/health")
            if health:
                st.success("✅ System is healthy")
                st.json(health)
    
    with col2:
        st.subheader("Trust Events")
        if st.button("Get Trust Events"):
            events = make_api_request("/trust_events")
            if events and events.get("trust_events"):
                df = pd.DataFrame(events["trust_events"])
                st.dataframe(df)
            else:
                st.info("No trust events found")
        
        if st.button("Clear Trust Events"):
            result = make_api_request("/trust_events", method="DELETE")
            if result:
                st.success(f"✅ {result['message']}")

# Manual Analysis page
elif page == "Manual Analysis":
    st.header("Manual Product Analysis")
    
    st.write("Enter product details for fraud analysis:")
    
    with st.form("analysis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            product_id = st.text_input("Product ID", value="test_prod_001")
            seller_id = st.text_input("Seller ID", value="test_seller_001") 
            product_name = st.text_input("Product Name", value="Test Product")
            price = st.number_input("Price", min_value=0.0, value=100.0)
            quantity = st.number_input("Quantity", min_value=0, value=10)
        
        with col2:
            image_url = st.text_input("Image URL", value="http://example.com/image.jpg")
            perceptual_score = st.slider("Perceptual AI Score", 0.0, 1.0, 0.8)
            return_ratio = st.slider("Return/Refund Ratio", 0.0, 1.0, 0.05)
            account_age = st.number_input("Seller Account Age (days)", min_value=0, value=300)
            total_sales = st.number_input("Seller Total Sales", min_value=0, value=100)
        
        # Advanced options
        with st.expander("Advanced Options"):
            historical_prices = st.text_input("Historical Prices (comma-separated)", value="95,100,105")
            reviews = st.text_area("Recent Reviews (one per line)", value="Great product!\nFast shipping!")
            complaints = st.text_input("Complaint Types (comma-separated)", value="")
        
        submitted = st.form_submit_button("Analyze Product")
        
        if submitted:
            # Parse inputs
            hist_prices = [float(x.strip()) for x in historical_prices.split(",") if x.strip()]
            review_list = [r.strip() for r in reviews.split("\n") if r.strip()]
            complaint_list = [{"type": c.strip()} for c in complaints.split(",") if c.strip()]
            
            # Build request data
            analysis_data = {
                "data": {
                    "product_id": product_id,
                    "seller_id": seller_id,
                    "product_name": product_name,
                    "price": price,
                    "quantity": quantity,
                    "product_image_url": image_url,
                    "perceptual_ai_score": perceptual_score,
                    "return_refund_ratios": return_ratio,
                    "historical_prices": hist_prices,
                    "recent_reviews": review_list,
                    "complaint_history": complaint_list,
                    "seller_history": {
                        "account_age_days": account_age,
                        "total_sales": total_sales,
                        "category_changes": 0
                    },
                    "market_benchmarks": {product_name: price * 1.1},
                    "reviewer_trust_scores": {"user1": 0.8, "user2": 0.9},
                    "listing_patterns": {}
                }
            }
            
            with st.spinner("Analyzing product..."):
                result = make_api_request("/analyze", method="POST", data=analysis_data)
                
                if result:
                    st.success("✅ Analysis complete!")
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        fraud_score = result.get("fraud_score", 0)
                        st.metric("Fraud Score", f"{fraud_score:.3f}")
                        
                        if fraud_score > 0.7:
                            st.error("🚨 High fraud risk!")
                        elif fraud_score > 0.3:
                            st.warning("⚠️ Medium fraud risk")
                        else:
                            st.success("✅ Low fraud risk")
                    
                    with col2:
                        details = result.get("details", {})
                        trust_score = details.get("trust_score", 0)
                        st.metric("Trust Score", f"{trust_score:.3f}")
                    
                    with col3:
                        confidence = details.get("confidence", 0)
                        st.metric("Confidence", f"{confidence:.3f}")
                    
                    # Detailed results
                    st.subheader("Analysis Details")
                    if details:
                        st.json(details)

# Simulation page
elif page == "Simulation":
    st.header("Fraud Detection Simulation")
    
    st.write("Run the CrewAI system on 10 synthetic product listings to demonstrate behavior.")
    
    if st.button("🚀 Run Simulation"):
        with st.spinner("Running simulation on 10 synthetic products..."):
            results = make_api_request("/simulate", method="POST")
            
            if results:
                st.success(f"✅ Simulation complete! Analyzed {len(results)} products.")
                
                # Convert to DataFrame for better display
                df_data = []
                for result in results:
                    df_data.append({
                        "Product ID": result["product_id"],
                        "Trust Score": f"{result['details']['trust_score']:.3f}",
                        "Fraud Risk": "🚨 High" if result['details']['trust_score'] < 0.3 else 
                                    "⚠️ Medium" if result['details']['trust_score'] < 0.7 else "✅ Low",
                        "Confidence": f"{result['details']['confidence']:.3f}",
                        "Signals": len(result['details']['fraud_signals']),
                        "Top Signal": result['details']['fraud_signals'][0] if result['details']['fraud_signals'] else "None"
                    })

                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # Detailed results
                st.subheader("Detailed Results")
                for result in results:
                    with st.expander(f"Product {result['product_id']} - Trust: {result['details']['trust_score']:.3f}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Fraud Signals:**")
                            fraud_signals = result.get("details", {}).get("fraud_signals", [])
                            if fraud_signals:
                                for signal in fraud_signals:
                                    st.write(f"• {signal}")
                            else:
                                st.write("No fraud signals detected")

                        with col2:
                            st.write("**Explanation:**")
                            st.write(result.get("details", {}).get("explanation", "No explanation available"))

# System Health page
elif page == "System Health":
    st.header("System Health & Monitoring")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("API Health")
        if st.button("Check API Status"):
            health = make_api_request("/health")
            if health:
                st.json(health)
        
        st.subheader("Pattern Memory")
        if st.button("Check Pattern Memory"):
            try:
                with open("pattern_memory.json", "r") as f:
                    patterns = json.load(f)
                st.write(f"Found {len(patterns)} stored patterns")
                if patterns:
                    df_patterns = pd.DataFrame(patterns)
                    st.dataframe(df_patterns)
            except FileNotFoundError:
                st.info("No pattern memory file found")
            except Exception as e:
                st.error(f"Error reading pattern memory: {e}")
    
    with col2:
        st.subheader("Learned Patterns")
        if st.button("Check Learned Patterns"):
            try:
                with open("learned_patterns.json", "r") as f:
                    learned = json.load(f)
                st.write(f"Found {len(learned)} learned patterns")
                if learned:
                    df_learned = pd.DataFrame(learned)
                    st.dataframe(df_learned)
            except FileNotFoundError:
                st.info("No learned patterns file found")
            except Exception as e:
                st.error(f"Error reading learned patterns: {e}")
        
        st.subheader("System Logs")
        if st.button("Show Recent Activity"):
            # This would show recent log entries in a real system
            st.info("Log monitoring would be implemented here")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**CrewAI Fraud Detection System**")
st.sidebar.markdown("Multi-agent AI for e-commerce security")