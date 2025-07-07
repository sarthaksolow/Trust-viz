import requests
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from datetime import datetime
import streamlit as st
import pandas as pd
import random
import plotly.graph_objects as go
from plotly.subplots import make_subplots

console = Console()

def create_analysis_table(title, data):
    """Create a rich table for analysis results"""
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")
    
    for row in data:
        table.add_row(row[0], row[1], row[2])
    
    return table

def simulate_analysis_progress(description):
    """Show a progress bar for analysis"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(description, total=100)
        while not progress.finished:
            progress.update(task, advance=20)
            time.sleep(0.5)

def demo_legitimate_product():
    """Demo with a legitimate Nike product"""
    console.print(Panel.fit("🏃 Scenario 1: Premium Brand Product Analysis", 
                          subtitle="Testing a legitimate Nike product listing"))
    
    legitimate_data = {
        "seller_id": "trusted_seller_123",
        "product_id": "nike_air_001",
        "product_name": "Nike Air Max 2023",
        "quantity": 10,
        "price": 199.99,
        "product_image_url": "test_images/placeholder_brand.jpg"
    }

    # Step 1: Seller Profile
    seller_data = [
        ("Account Age", "2.5 years", "✅ VERIFIED"),
        ("Transaction History", "1,523 sales", "✅ GOOD"),
        ("Return Rate", "2.3%", "✅ EXCELLENT"),
        ("Customer Rating", "4.8/5.0", "✅ HIGH"),
        ("Verification Status", "Identity Verified", "✅ VERIFIED")
    ]
    console.print(create_analysis_table("👤 Seller Profile Analysis", seller_data))

    # Step 2: Product Analysis
    simulate_analysis_progress("🔍 Analyzing product listing...")
    
    product_data = [
        ("Price Analysis", "$199.99", "✅ MARKET MATCH"),
        ("Stock Level", "10 units", "✅ NORMAL"),
        ("Category", "Premium Footwear", "✅ VERIFIED"),
        ("Brand Match", "Nike Official", "✅ AUTHENTIC")
    ]
    console.print(create_analysis_table("📦 Product Listing Analysis", product_data))

    # Step 3: Image Analysis
    simulate_analysis_progress("📸 Performing image authenticity check...")
    
    image_data = [
        ("Hash Match", "98%", "✅ AUTHENTIC"),
        ("Quality Score", "0.95/1.00", "✅ HIGH QUALITY"),
        ("Brand Pattern", "Detected", "✅ VERIFIED"),
        ("Metadata", "Original", "✅ UNMODIFIED")
    ]
    console.print(create_analysis_table("🖼️ Image Analysis Results", image_data))

def demo_counterfeit_product():
    """Demo with a sophisticated counterfeit attempt"""
    console.print(Panel.fit("🚨 Scenario 2: Sophisticated Counterfeit Detection", 
                          subtitle="High-risk listing detection"))
    
    suspicious_data = {
        "seller_id": "new_seller_456",
        "product_id": "luxury_bag_001",
        "product_name": "Designer Luxury Handbag",
        "quantity": 100,
        "price": 299.99,
        "product_image_url": "test_images/seller.jpg"
    }

    # Step 1: Risk Indicators
    risk_data = [
        ("Account Age", "15 days", "⚠️ NEW"),
        ("Listing Count", "143 items", "🚨 SUSPICIOUS"),
        ("Price Delta", "-85% vs Market", "🚨 SUSPICIOUS"),
        ("Stock Level", "100 units", "🚨 UNUSUAL")
    ]
    console.print(create_analysis_table("🚩 Risk Indicator Analysis", risk_data))

    # Step 2: Image Analysis
    simulate_analysis_progress("🔍 Running deep image authentication...")
    
    image_analysis = [
        ("Hash Match", "12%", "🚨 MISMATCH"),
        ("Quality Score", "0.45/1.00", "⚠️ LOW QUALITY"),
        ("Manipulation", "Detected", "🚨 MODIFIED"),
        ("Brand Pattern", "Not Found", "🚨 SUSPICIOUS")
    ]
    console.print(create_analysis_table("📸 Image Authentication Results", image_analysis))

def demo_review_manipulation():
    """Demo detecting fake reviews"""
    console.print(Panel.fit("🤖 Scenario 3: Review Manipulation Detection", 
                          subtitle="AI-powered review authenticity analysis"))

    # Step 1: Review Pattern Analysis
    simulate_analysis_progress("📊 Analyzing review patterns...")
    
    review_data = [
        ("Review Burst", "52 in 1 hour", "🚨 SUSPICIOUS"),
        ("Text Similarity", "87% match", "🚨 BOT-LIKE"),
        ("IP Analysis", "Single Source", "🚨 SUSPICIOUS"),
        ("Time Pattern", "Non-random", "⚠️ UNUSUAL")
    ]
    console.print(create_analysis_table("📝 Review Pattern Analysis", review_data))

    # Step 2: Content Analysis
    content_data = [
        ("Sentiment", "Overly Positive", "⚠️ SUSPICIOUS"),
        ("Language", "Template-like", "🚨 BOT DETECTED"),
        ("User History", "No Previous", "⚠️ NEW ACCOUNTS"),
        ("Purchase Verify", "None", "🚨 UNVERIFIED")
    ]
    console.print(create_analysis_table("🔍 Review Content Analysis", content_data))

def demo_blockchain_trust():
    """Demo the blockchain trust ledger"""
    console.print(Panel.fit("⛓️ Scenario 4: Trust Ledger Demonstration", 
                          subtitle="Blockchain-based trust score tracking"))

    # Step 1: Trust Score Components
    trust_data = [
        ("Seller Score", "15/100", "🚨 HIGH RISK"),
        ("Product Score", "23/100", "🚨 SUSPICIOUS"),
        ("Review Score", "12/100", "🚨 FRAUDULENT"),
        ("Overall Trust", "16/100", "🚨 BLACKLIST")
    ]
    console.print(create_analysis_table("📊 Trust Score Analysis", trust_data))

    # Step 2: Blockchain Record
    simulate_analysis_progress("💾 Recording to immutable ledger...")
    
    blockchain_data = [
        ("Transaction ID", "0x7f2c8d...", "✅ CONFIRMED"),
        ("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "✅ RECORDED"),
        ("Block Height", "#1,234,567", "✅ IMMUTABLE"),
        ("Network Status", "Consensus", "✅ VERIFIED")
    ]
    console.print(create_analysis_table("⛓️ Blockchain Record", blockchain_data))

def simulate_analysis(product_data):
    """Simulate the analysis process"""
    # Perceptual AI Analysis
    quality_score = random.uniform(0.3, 0.9)
    hash_match = random.uniform(0.2, 0.95)
    
    # Review Analysis
    review_score = random.uniform(0.4, 0.9)
    
    # Seller Analysis
    seller_score = random.uniform(0.3, 0.95)
    
    # Overall Trust Score
    trust_score = (quality_score + hash_match + review_score + seller_score) / 4
    
    return {
        'quality_score': quality_score,
        'hash_match': hash_match,
        'review_score': review_score,
        'seller_score': seller_score,
        'trust_score': trust_score,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def create_blockchain_visualization(num_blocks=5):
    blocks = []
    prev_hash = "0000"
    for i in range(num_blocks):
        block = {
            'index': i,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'hash': ''.join(random.choices('0123456789abcdef', k=8)),
            'prev_hash': prev_hash,
            'data': f"Product Analysis #{random.randint(1000, 9999)}"
        }
        blocks.append(block)
        prev_hash = block['hash']
    return blocks

def simulate_swarm_analysis():
    return {
        'image_score': random.uniform(0.3, 0.9),
        'review_score': random.uniform(0.4, 0.9),
        'seller_score': random.uniform(0.5, 0.95),
        'price_analysis': random.uniform(0.3, 0.9)
    }

def main():
    # Title Banner
    console.print(Panel.fit(
        "[bold blue]🛡️ TrustViz: AI-Powered Fraud Detection System[/bold blue]\n" +
        "[italic]Protecting E-commerce Through Multi-Agent AI and Blockchain[/italic]",
        box=box.DOUBLE_EDGE
    ))
    
    # System Status Check
    console.print("\n🔄 Performing System Health Check...")
    services = [
        ("Data Ingestion", "ONLINE", "✅"),
        ("Swarm Intelligence", "ONLINE", "✅"),
        ("Perceptual AI", "ONLINE", "✅"),
        ("Trust Ledger", "ONLINE", "✅"),
        ("Review Analyzer", "ONLINE", "✅")
    ]
    console.print(create_analysis_table("🖥️ System Status", services))
    
    # Run Demo Scenarios
    console.print("\n[bold]Starting Comprehensive Fraud Detection Demo[/bold]")
    
    demo_legitimate_product()
    time.sleep(1)
    console.print("\n" + "="*80 + "\n")
    
    demo_counterfeit_product()
    time.sleep(1)
    console.print("\n" + "="*80 + "\n")
    
    demo_review_manipulation()
    time.sleep(1)
    console.print("\n" + "="*80 + "\n")
    
    demo_blockchain_trust()

    # Summary
    console.print(Panel.fit(
        "🎯 Key Features Demonstrated:\n" +
        "• Real-time Multi-factor Analysis\n" +
        "• AI-powered Image Authentication\n" +
        "• Review Manipulation Detection\n" +
        "• Blockchain Trust Ledger\n" +
        "• Swarm Intelligence Coordination",
        title="Demo Summary",
        box=box.DOUBLE
    ))

    # Set page config
    st.set_page_config(
        page_title="TrustViz Demo",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .data-flow {
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 5px;
            margin: 10px 0;
        }
        .kafka-message {
            font-family: monospace;
            padding: 5px;
            background-color: #e1e4e8;
            border-radius: 3px;
        }
        .step-box {
            padding: 20px;
            border-radius: 10px;
            background-color: #f0f2f6;
            margin: 10px 0;
            border-left: 5px solid #4CAF50;
        }
        .flow-arrow {
            text-align: center;
            font-size: 24px;
            color: #666;
        }
        .blockchain-block {
            padding: 15px;
            background-color: #e1e4e8;
            border-radius: 8px;
            margin: 5px 0;
            font-family: monospace;
        }
        </style>
    """, unsafe_allow_html=True)

    # Simulated data storage
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'trust_scores' not in st.session_state:
        st.session_state.trust_scores = {}
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}

    # Header
    st.markdown("<h1 style='text-align: center;'>🛡️ TrustViz: Multi-Agent Fraud Detection System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Protecting E-commerce Through Multi-Agent AI and Blockchain</p>", unsafe_allow_html=True)

    # System Status Dashboard
    st.markdown("### 🖥️ System Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Data Ingestion", "✅ Active", "5ms")
    col2.metric("Swarm Intelligence", "✅ Active", "8ms")
    col3.metric("Perceptual AI", "✅ Active", "12ms")
    col4.metric("Review Analyzer", "✅ Active", "7ms")
    col5.metric("Trust Ledger", "✅ Active", "3ms")

    # Main Interface
    st.markdown("### 🔄 System Workflow Demonstration")

    # Step 1: Data Ingestion
    st.markdown("#### Step 1: Data Ingestion")
    col1, col2 = st.columns(2)
    
    with col1:
        seller_id = st.text_input("Seller ID", value="seller_123")
        product_name = st.text_input("Product Name", value="Luxury Brand Bag")
        price = st.number_input("Price ($)", value=299.99, step=0.01)
        quantity = st.number_input("Quantity", value=10, step=1)

    with col2:
        st.markdown("### 📸 Product Image")
        image_file = st.file_uploader("Upload Product Image", type=['jpg', 'png'])

    if st.button("Start Analysis"):
        # Create placeholder containers for each step
        ingestion_container = st.empty()
        swarm_container = st.empty()
        perceptual_container = st.empty()
        review_container = st.empty()
        final_container = st.empty()
        blockchain_container = st.empty()

        # Step 1: Data Ingestion
        with ingestion_container.container():
            st.markdown("### 📥 Data Ingestion Service")
            st.info("Receiving product data...")
            time.sleep(1)
            st.success("✅ Data received and validated")
            st.json({
                "seller_id": seller_id,
                "product_name": product_name,
                "price": price,
                "quantity": quantity,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            time.sleep(1)

        # Step 2: Initial Swarm Analysis
        with swarm_container.container():
            st.markdown("### 🐝 Swarm Intelligence - Initial Assessment")
            st.info("Coordinating analysis tasks...")
            time.sleep(1)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Price Risk", f"{random.uniform(0.3, 0.9):.2f}")
                st.metric("Quantity Risk", f"{random.uniform(0.3, 0.9):.2f}")
            with col2:
                st.metric("Seller Risk", f"{random.uniform(0.3, 0.9):.2f}")
                st.metric("Initial Risk Score", f"{random.uniform(0.3, 0.9):.2f}")
            time.sleep(1)

        # Step 3: Perceptual AI Analysis
        with perceptual_container.container():
            st.markdown("### 🔍 Perceptual AI Analysis")
            st.info("Analyzing product images...")
            
            # Simulate analysis progress
            progress_bar = st.progress(0)
            for i in range(100):
                progress_bar.progress(i + 1)
                time.sleep(0.02)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Image Quality", f"{random.uniform(0.3, 0.9):.2f}")
            with col2:
                st.metric("Brand Match", f"{random.uniform(0.3, 0.9):.2f}")
            with col3:
                st.metric("Authenticity Score", f"{random.uniform(0.3, 0.9):.2f}")
            time.sleep(1)

        # Step 4: Review Analysis
        with review_container.container():
            st.markdown("### 📝 Review Analysis")
            st.info("Analyzing review patterns...")
            
            review_metrics = {
                "Review Count": random.randint(10, 100),
                "Average Rating": round(random.uniform(3.5, 5.0), 1),
                "Verified Purchases": f"{random.randint(60, 100)}%",
                "Suspicious Patterns": f"{random.randint(0, 20)}%"
            }
            
            cols = st.columns(len(review_metrics))
            for col, (metric, value) in zip(cols, review_metrics.items()):
                col.metric(metric, value)
            time.sleep(1)

        # Step 5: Final Swarm Decision
        with final_container.container():
            st.markdown("### 🤖 Final Swarm Decision")
            
            final_score = random.uniform(0.3, 0.9)
            st.progress(final_score)
            
            if final_score < 0.5:
                st.error("🚨 High Risk: Potential counterfeit detected")
            elif final_score < 0.7:
                st.warning("⚠️ Medium Risk: Some suspicious patterns")
            else:
                st.success("✅ Low Risk: Likely authentic product")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Image Trust", f"{random.uniform(0.3, 0.9):.2f}")
            col2.metric("Seller Trust", f"{random.uniform(0.3, 0.9):.2f}")
            col3.metric("Review Trust", f"{random.uniform(0.3, 0.9):.2f}")
            col4.metric("Final Trust Score", f"{final_score:.2f}")
            time.sleep(1)

        # Step 6: Blockchain Recording
        with blockchain_container.container():
            st.markdown("### ⛓️ Trust Ledger Recording")
            
            # Create blockchain visualization
            blocks = create_blockchain_visualization()
            
            # Display the latest block being added
            st.info("Recording trust score in blockchain...")
            time.sleep(1)
            
            for block in blocks:
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.markdown(f"**Block #{block['index']}**")
                    with col2:
                        st.code(f"""
Hash: {block['hash']}
Prev: {block['prev_hash']}
Time: {block['timestamp']}
Data: {block['data']}
                        """)
                    
                    if block['index'] < len(blocks) - 1:
                        st.markdown("⬇️")
            
            st.success("✅ Transaction recorded in Trust Ledger")

if __name__ == "__main__":
    main()