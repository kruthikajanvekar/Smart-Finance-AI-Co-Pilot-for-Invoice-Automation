# Save as: app/enhanced_streamlit_app.py

import streamlit as st
import pandas as pd
import sys
import os
import json
from datetime import datetime
from src.logger.logger import get_logger
logger = get_logger(__name__)


# Add parent directory to path to find src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


from src.agents.invoice_followup_agent import InvoiceFollowupAgent
from src.agents.three_way_matching_agent import ThreeWayMatchingAgent
from src.agents.vendor_query_agent import VendorQueryAgent
from config import Config

def main():
    st.set_page_config(
        page_title="CatalystAI - Invoice Automation",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize all agents
    init_agents()
    
    # Sidebar Navigation
    create_sidebar()
    
    # Header
    st.title("⚡ CatalystAI")
    st.markdown("*AI-Powered Invoice Automation & Collections*")
    st.markdown("---")
    
    # Route to pages
    route_pages()

def init_agents():
    """Initialize all AI agents"""
    
    if 'invoice_agent' not in st.session_state:
        st.session_state.invoice_agent = InvoiceFollowupAgent()
    
    if 'matching_agent' not in st.session_state:
        st.session_state.matching_agent = ThreeWayMatchingAgent()
    
    if 'vendor_agent' not in st.session_state:
        st.session_state.vendor_agent = VendorQueryAgent()

def create_sidebar():
    """Create enhanced sidebar with all modules"""
    
    st.sidebar.title("🎛️ Control Center")
    
    # Module Selection
    st.sidebar.markdown("### 🚀 AI Modules")
    
    page = st.sidebar.radio(
        "Select Module:",
        [
            "🏠 Executive Dashboard",
            "🤖 AI Follow-ups", 
            "⚖️ 3-Way Matching",
            "🏢 Vendor Portal",
            "🔌 ERP Integration",
            "📊 Advanced Analytics",
            "⚙️ Settings"
        ],
        key="page_selector"
    )
    
    # API Configuration
    with st.sidebar.expander("🔑 API Configuration", expanded=False):
        st.markdown("### 🤖 Google Gemini API")
        
        api_key_input = st.text_input(
            "Google API Key", 
            type="password",
            value=Config.GOOGLE_API_KEY if Config.GOOGLE_API_KEY else "",
            help="Get from: https://aistudio.google.com/app/apikey"
        )
        
        if api_key_input:
            Config.GOOGLE_API_KEY = api_key_input
            st.success("✅ Google API Key configured")
        elif Config.GOOGLE_API_KEY:
            st.success("✅ API Key loaded from environment (.env)")
        else:
            st.warning("⚠️ No API Key found. Set GOOGLE_API_KEY in .env or enter here")
        
        st.markdown("---")
        st.markdown("### 📊 Current Configuration")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("🔥 Free Tier", "✅ Enabled" if Config.FREE_TIER_MODE else "❌ Disabled")
        with col_b:
            st.metric("⏱️ Request Cap", f"{Config.FREE_TIER_CAP}/min")
        
        st.markdown("---")
        st.markdown("### 🔌 ERP Connections")
        st.info("📱 QuickBooks: Not Connected (Configure in 🔌 ERP Integration)")
        st.info("🏭 SAP: Not Connected (Configure in 🔌 ERP Integration)")

    
    # Quick Stats
    with st.sidebar.expander("📈 Quick Stats", expanded=True):
        try:
            df = st.session_state.invoice_agent.load_invoice_data()
            total_overdue = df[df['status'] == 'overdue']['invoice_amount'].sum()
            overdue_count = len(df[df['status'] == 'overdue'])
            
            st.metric("💸 Total Overdue", f"${total_overdue:,.2f}")
            st.metric("📄 Count", overdue_count)
            
        except Exception as e:
            st.error("Unable to load quick stats")
    
    # Store selected page
    st.session_state.current_page = page

def route_pages():
    """Route to different pages based on selection"""
    
    page = st.session_state.get('current_page', '🏠 Executive Dashboard')
    
    if page == "🏠 Executive Dashboard":
        executive_dashboard()
    elif page == "🤖 AI Follow-ups":
        ai_followups_page()
    elif page == "⚖️ 3-Way Matching":
        three_way_matching_page()
    elif page == "🏢 Vendor Portal":
        vendor_portal_page()
    elif page == "🔌 ERP Integration":
        erp_integration_page()
    elif page == "📊 Advanced Analytics":
        advanced_analytics_page()
    elif page == "⚙️ Settings":
        settings_page()

def executive_dashboard():
    """Executive-level dashboard with key metrics"""
    
    st.header("🏠 Executive Dashboard")
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    try:
        df = st.session_state.invoice_agent.load_invoice_data()
        
        with col1:
            total_outstanding = df[df['status'] == 'overdue']['invoice_amount'].sum()
            st.metric("💸 Outstanding", f"${total_outstanding:,.2f}", delta="↑ 12%")
        
        with col2:
            overdue_count = len(df[df['status'] == 'overdue'])
            st.metric("📄 Overdue", overdue_count, delta="↓ 3")
        
        with col3:
            avg_days = df[df['status'] == 'overdue']['days_overdue'].mean()
            st.metric("⏰ Avg Days", f"{avg_days:.0f}", delta="↓ 2 days")
        
        with col4:
            # Simulated automation savings
            st.metric("🤖 AI Savings", "$45,200", delta="↑ $8,500")
        
        with col5:
            # Simulated processing time
            st.metric("⚡ Process Time", "2.3 min", delta="↓ 87%")
    
    except Exception as e:
        st.error("Unable to load dashboard metrics")
    
    # Action Items and Insights
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚨 Priority Action Items")
        
        action_items = [
            {"priority": "🔴", "item": "3 high-value invoices >90 days overdue", "amount": "$125,000", "action": "Escalate"},
            {"priority": "🟡", "item": "12 invoices pending 3-way matching", "amount": "$67,500", "action": "Review"},
            {"priority": "🟢", "item": "AI generated 28 follow-up emails", "amount": "$340,000", "action": "Approve"},
        ]
        
        for item in action_items:
            with st.expander(f"{item['priority']} {item['item']}", expanded=False):
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.write(f"**Impact:** {item['amount']}")
                    st.write(f"**Recommended Action:** {item['action']}")
                with col_b:
                    if st.button(f"Take Action", key=f"action_{item['item'][:20]}"):
                        st.success("Action initiated!")
    
    with col2:
        st.subheader("🧠 AI Insights")
        
        insights = [
            "📈 Collection rate improved 15% this month",
            "🎯 Voice queries reduced response time by 78%", 
            "⚡ 3-way matching automation saves 2000+ hours",
            "🔍 Fraud detection prevented $12,500 in errors"
        ]
        
        for insight in insights:
            st.info(insight)
        
        st.markdown("---")
        st.markdown("**🔄 Last Updated:** " + datetime.now().strftime("%H:%M:%S"))

def ai_followups_page():
    """Enhanced AI follow-ups page"""
    
    st.header("🤖 AI-Generated Follow-ups")
    
    # Enhanced configuration
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Smart Configuration")
        
        num_followups = st.slider("Number of Follow-ups", 1, 20, 1)
        generation_mode = st.radio("Generation Mode:", ["Template (instant)", "LLM (may be slow / quota)"], index=0)
        use_template_only = generation_mode.startswith("Template")
        # Warn users about free-tier caps when selecting more than allowed
        if getattr(Config, "FREE_TIER_MODE", False) and num_followups > getattr(Config, "FREE_TIER_CAP", 1):
            st.warning(
                f"Free-tier mode is active: requests will be capped to {Config.FREE_TIER_CAP} follow-up(s) per run. "
                "If you have billing enabled, set FREE_TIER_MODE=false in your .env to disable this cap."
            )
        
        # AI-powered filters
        st.write("**🎯 AI Targeting:**")
        use_ai_priority = st.checkbox("Use AI Priority Scoring", value=True)
        use_customer_intelligence = st.checkbox("Apply Customer Intelligence", value=True)
        
        # Risk-based filtering
        st.write("**⚠️ Risk Filters:**")
        min_risk_score = st.slider("Minimum Risk Score", 0.0, 1.0, 0.3)
        
        # Advanced options
        with st.expander("🔬 Advanced Options"):
            tone_preference = st.selectbox("Default Tone", ["Auto-Select", "Professional", "Friendly", "Firm"])
            follow_up_timing = st.selectbox("Follow-up Timing", ["AI Optimized", "24 Hours", "48 Hours", "Weekly"])
    
    with col2:
        if st.button("🚀 Generate Smart Follow-ups", type="primary", use_container_width=True):
            with st.spinner("🧠 AI is analyzing customer behavior patterns..."):
                try:
                    # Enhanced follow-up generation with new parameters
                    followups = st.session_state.invoice_agent.generate_batch_followups(num_followups, use_template_only=use_template_only)
                    
                    if followups:
                        st.success(f"✅ Generated {len(followups)} smart follow-ups!")
                        display_enhanced_followups(followups)
                    else:
                        st.info("🎉 No overdue invoices requiring follow-up!")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def three_way_matching_page():
    """3-way matching automation page"""
    
    st.header("⚖️ 3-Way Matching AI")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔍 Matching Controls")
        
        # Mock invoice selection
        invoice_options = ["INV2024001", "INV2024002", "INV2024003", "INV2024004"]
        selected_invoice = st.selectbox("Select Invoice to Match:", invoice_options)
        
        tolerance_settings = st.expander("⚙️ Tolerance Settings")
        with tolerance_settings:
            quantity_tolerance = st.slider("Quantity Tolerance %", 0.0, 10.0, 5.0)
            price_tolerance = st.slider("Price Tolerance %", 0.0, 5.0, 2.0)
        
        if st.button("🔍 Perform 3-Way Match", type="primary"):
            with st.spinner("🤖 AI is analyzing documents..."):
                # Simulate matching process
                result = simulate_three_way_match(selected_invoice)
                st.session_state.matching_result = result
    
    with col2:
        if 'matching_result' in st.session_state:
            result = st.session_state.matching_result
            
            st.subheader(f"📋 Matching Results: {selected_invoice}")
            
            # Overall status
            status_colors = {
                "perfect_match": "🟢",
                "acceptable_match": "🟡", 
                "review_required": "🟠",
                "reject_match": "🔴"
            }
            
            status = result['status']
            st.markdown(f"### {status_colors.get(status, '⚪')} {status.replace('_', ' ').title()}")
            st.metric("Match Score", f"{result['overall_score']:.1f}%")
            
            # Detailed breakdown
            st.subheader("📊 Detailed Analysis")
            
            checks = [
                ("Vendor Match", result['vendor_score'], "🏢"),
                ("Quantity Match", result['quantity_score'], "📦"),
                ("Price Match", result['price_score'], "💰"),
                ("Date Validation", result['date_score'], "📅")
            ]
            
            for check_name, score, icon in checks:
                col_check, col_score = st.columns([3, 1])
                with col_check:
                    st.write(f"{icon} {check_name}")
                with col_score:
                    color = "green" if score > 90 else "orange" if score > 70 else "red"
                    st.markdown(f"<span style='color:{color}'>{score:.1f}%</span>", unsafe_allow_html=True)
            
            # AI Recommendation
            st.subheader("🧠 AI Recommendation")
            st.info(result['recommendation'])
            
            # Action buttons
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("✅ Approve"):
                    st.success("Invoice approved for payment!")
            with col_b:
                if st.button("👁️ Review"):
                    st.info("Flagged for manual review")
            with col_c:
                if st.button("❌ Reject"):
                    st.error("Invoice rejected")

def vendor_portal_page():
    """Vendor self-service portal simulation"""
    
    st.header("🏢 Vendor Portal & Query Assistant")
    
    with st.container():
        st.subheader("💬 Ask Our AI Assistant")
        
        # Vendor identification
        vendor_email = st.text_input("Your Email:", placeholder="vendor@company.com")
        
        # Query input
        vendor_query = st.text_area(
            "Your Question:",
            placeholder="e.g., 'What's the status of invoice INV001?' or 'When will I be paid?'",
            height=100
        )
        
        if st.button("🤖 Ask Assistant", type="primary"):
            if vendor_query.strip():
                with st.spinner("🤖 Processing your query..."):
                    try:
                        response = st.session_state.vendor_agent.process_vendor_query(
                            vendor_query, vendor_email
                        )
                        
                        st.subheader("🤖 Assistant Response:")
                        
                        if response.get('success', False):
                            st.success(response.get('response', 'No response'))
                        else:
                            st.warning(response.get('response', 'Unable to process query'))
                            
                    except Exception as e:
                        st.error(f"Error processing query: {str(e)}")
    


def erp_integration_page():
    """ERP integration management"""
    
    st.header("🔌 ERP Integration Hub")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🏭 Supported ERPs")
        
        erp_systems = [
            {"name": "QuickBooks Online", "status": "Not Connected", "color": "red"},
            {"name": "SAP Business One", "status": "Not Connected", "color": "red"},
        ]
        
        for erp in erp_systems:
            with st.expander(f"📱 {erp['name']} - {erp['status']}"):
                st.info("Configure your credentials to connect")
                
                if erp['name'] == "QuickBooks Online":
                    client_id = st.text_input("Client ID", key=f"qb_client")
                    client_secret = st.text_input("Client Secret", type="password", key=f"qb_secret")
                    
                    if st.button(f"Connect to {erp['name']}", key=f"connect_qb"):
                        st.success("Connection successful! (Demo)")
                
                elif erp['name'] == "SAP Business One":
                    server_url = st.text_input("Server URL", key="sap_url")
                    database = st.text_input("Database", key="sap_db") 
                    
                    if st.button(f"Connect to {erp['name']}", key="connect_sap"):
                        st.success("Connection successful! (Demo)")
        
        # Coming Soon Section
        st.markdown("---")
        st.subheader("🚀 Coming Soon")
        coming_soon = [
            {"name": "NetSuite", "icon": "☁️"},
            {"name": "Xero", "icon": "💼"},
        ]
        for erp in coming_soon:
            st.info(f"{erp['icon']} {erp['name']} - Integration coming soon")

    
    with col2:
        st.subheader("🔄 Data Synchronization")
        
        # Sync status
        st.write("**Last Sync:** Never")
        st.write("**Sync Frequency:** Manual")
        
        # Sync controls
        if st.button("🔄 Sync All Data", type="primary"):
            with st.spinner("Syncing data from connected ERPs..."):
                # Simulate sync process
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                st.success("✅ Sync completed! 0 invoices, 0 customers updated.")
        
        # Sync history
        st.subheader("📋 Sync History")
        st.info("No sync history available")
        
        # Data mapping
        with st.expander("⚙️ Field Mapping Configuration"):
            st.write("Configure how ERP fields map to our system:")
            
            mapping_options = {
                "Invoice Number": st.text_input("ERP Invoice Field", value="DocNum"),
                "Customer Name": st.text_input("ERP Customer Field", value="CardName"),
                "Amount": st.text_input("ERP Amount Field", value="DocTotal"),
            }

def advanced_analytics_page():
    """Advanced analytics and reporting"""
    
    st.header("📊 Advanced Analytics")
    
    # Import and display analytics
    try:
        from analytics_dashboard import create_analytics_dashboard
        create_analytics_dashboard()
    except Exception as e:
        st.error("Analytics module not available")

def settings_page():
    """Settings and configuration"""
    
    st.header("⚙️ System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Business Rules")
        
        overdue_threshold = st.number_input("Overdue Threshold (days)", value=30)
        firm_reminder = st.number_input("Firm Reminder (days)", value=45)
        legal_escalation = st.number_input("Legal Escalation (days)", value=60)
        
        if st.button("💾 Save Rules"):
            st.success("✅ Business rules updated!")
    
    with col2:
        st.subheader("🤖 AI Configuration")
        
        model_choice = st.selectbox(
            "AI Model",
            [
                "gemini-2.5-pro (Recommended)",
                "gemini-2.1-flash",
                "gemini-2.0-pro"
            ],
            help="Free tier uses gemini-2.1-flash. Pro tier unlocks 2.5-pro for better quality."
        )
        
        if "2.5-pro" in model_choice:
            st.info("💡 Best for complex invoice analysis and personalized emails")
        elif "2.1-flash" in model_choice:
            st.info("⚡ Faster responses, ideal for free-tier API quotas")
        
        temperature = st.slider(
            "AI Creativity", 
            0.0, 1.0, 0.4,
            help="Lower = More consistent. Higher = More creative. (Default: 0.4 for finance)"
        )
        
        st.markdown("---")
        st.subheader("ℹ️ System Info")
        st.info(f"**Version:** {Config.VERSION}\n**Status:** ✅ Operational\n**LLM:** Google Gemini\n**Free Tier:** {'✅ Enabled' if Config.FREE_TIER_MODE else '❌ Disabled'}")

def display_enhanced_followups(followups):
    """Display enhanced follow-up results"""
    
    for i, followup in enumerate(followups, 1):
        with st.expander(f"📧 {followup['customer_name']} - ${followup['amount']:,.2f}", expanded=(i==1)):
            
            col_email, col_insights = st.columns([2, 1])
            
            with col_email:
                st.text_area(
                    "Generated Email:",
                    str(followup.get('generated_email', '')),
                    height=150,
                    key=f"email_{i}"
                )
                
            # Place action buttons in a single row at the expander level (avoids deep column nesting)
            action_cols = st.columns(3)
            with action_cols[0]:
                if st.button("✅ Approve", key=f"approve_{i}"):
                    st.success("Approved!")
            with action_cols[1]:
                if st.button("📤 Send", key=f"send_{i}"):
                    st.success("Sent!")
            with action_cols[2]:
                if st.button("⏰ Schedule", key=f"schedule_{i}"):
                    st.info("Scheduled!")
            
            with col_insights:
                st.write("**AI Insights:**")
                st.write(f"• Severity: {followup['severity']}")
                st.write(f"• Priority: {followup['priority_score']:.0f}")
                source = followup.get('generated_by', 'UNKNOWN')
                st.write(f"• Generated by: {source}")
                
                if followup.get('ai_insights'):
                    insights = followup['ai_insights']
                    if insights.get('recommendations'):
                        st.write(f"• Risk: {insights['recommendations'].get('escalation_risk', 'Unknown')}")

def simulate_three_way_match(invoice_id):
    """Simulate 3-way matching results"""
    
    return {
        'invoice_id': invoice_id,
        'status': 'acceptable_match',
        'overall_score': 87.5,
        'vendor_score': 95.0,
        'quantity_score': 88.0,
        'price_score': 92.0,
        'date_score': 75.0,
        'recommendation': 'Invoice matches within acceptable tolerances. Minor date sequence issue noted but not blocking. Recommend approval with notification to procurement team.'
    }

if __name__ == "__main__":
    main()