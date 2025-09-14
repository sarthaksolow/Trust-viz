import streamlit as st
import requests
import json

# Define the Swarm Intelligence service URL
SWARM_INTELLIGENCE_URL = "http://localhost:5001/analyze"  # Adjust if needed

# Synthetic product listings (for demonstration)
synthetic_listings = [
    { # Clean listing
        "product_id": "sim_prod_001", "seller_id": "sim_seller_001", "product_name": "Genuine Leather Wallet",
        "price": 45.00, "product_image_url": "http://example.com/img/wallet_clean.jpg", "quantity": 100,
        "historical_prices": [45.00, 46.00, 44.50], "market_benchmarks": {"Leather Wallet": 50.00},
        "recent_reviews": ["High quality!", "Exactly as described."], "reviewer_trust_scores": {"userA": 0.95, "userB": 0.92},
        "seller_history": {"account_age_days": 500, "total_sales": 200, "category_changes": 0},
        "listing_patterns": {}, "return_refund_ratios": 0.01, "complaint_history": [], "perceptual_ai_score": 0.98
    },
    { # Suspicious Price
        "product_id": "sim_prod_002", "seller_id": "sim_seller_002", "product_name": "Luxury Smartwatch",
        "price": 50.00, "product_image_url": "http://example.com/img/watch_cheap.jpg", "quantity": 10,
        "historical_prices": [500.00, 510.00, 495.00], "market_benchmarks": {"Luxury Smartwatch": 550.00},
        "recent_reviews": ["Amazing deal!", "Unbelievable price."], "reviewer_trust_scores": {"userC": 0.7, "userD": 0.6},
        "seller_history": {"account_age_days": 50, "total_sales": 5, "category_changes": 1},
        "listing_patterns": {}, "return_refund_ratios": 0.1, "complaint_history": [], "perceptual_ai_score": 0.8
    },
]

def fetch_fraud_assessment(product_data):
    """Fetches fraud assessment from the Swarm Intelligence service."""
    try:
        headers = {'Content-type': 'application/json'}
        response = requests.post(SWARM_INTELLIGENCE_URL, data=json.dumps(product_data), headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Swarm Intelligence: {e}")
        return None

st.title("TrustViz Swarm Intelligence Demo")

st.write("This Streamlit app demonstrates the fraud detection capabilities of the TrustViz Swarm Intelligence service.")

for listing in synthetic_listings:
    st.header(f"Product: {listing['product_name']} (ID: {listing['product_id']})")
    
    # Display product information
    st.subheader("Product Information")
    st.write(f"Seller ID: {listing['seller_id']}")
    st.write(f"Price: ${listing['price']}")
    st.write(f"Quantity: {listing['quantity']}")
    st.write(f"Image URL: {listing['product_image_url']}")

    # Fetch fraud assessment from Swarm Intelligence
    assessment = fetch_fraud_assessment(listing)

    if assessment:
        st.subheader("Fraud Assessment")
        st.write(f"Final Trust Score: {assessment.get('trust_score', 'N/A')}")
        st.write(f"Confidence: {assessment.get('confidence', 'N/A')}")
        st.write(f"Explanation: {assessment.get('reason', 'N/A')}")

        fraud_signals = assessment.get("fraud_signals", [])
        if fraud_signals:
            st.write("Fraud Signals:")
            for signal in fraud_signals:
                st.write(f"- {signal}")
    else:
        st.write("No fraud assessment available.")

    st.markdown("---") # Separator
