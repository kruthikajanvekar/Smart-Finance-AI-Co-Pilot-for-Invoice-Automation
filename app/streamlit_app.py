import streamlit as st
import pandas as pd
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.invoice_followup_agent import InvoiceFollowupAgent
from src.agents.voice_agent import VoiceFinanceAgent
from config import Config

def main():
    st.set_page_config(
        page_title="Finance AI Co-Pilot",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = InvoiceFollowupAgent()
    
    if 'voice_agent' not in st.session_state:
        st.session_state.voice_agent = VoiceFinanceAgent(st.session_state.agent)
    
    # Sidebar Navigation
    st.sidebar.title("🎛️ Navigation")
    
    page = st.sidebar.radio(
        "Choose a module:",
        ["🏠 Dashboard", "🤖 AI Follow-ups", "🎤 Voice Assistant", "📊 Analytics", "⚙️ Settings"]
    )
    
    # API Key Configuration
    with st.sidebar.expander("🔑 API Configuration"):
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            help="Enter your OpenAI API key to enable AI features"
        )
        
        if api_key:
            Config.OPENAI_API_KEY = api_key
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ API Key required for AI features")
    
    # Header
    st.title("💰 Finance AI Co-Pilot")
    st.markdown("*Intelligent Invoice-to-Cash Operations*")
    st.markdown("---")
    
    # Route to different pages
    if page == "🏠 Dashboard":
        dashboard_page()
    elif page == "🤖 AI Follow-ups":
        ai_followups_page(api_key)
    elif page == "🎤 Voice Assistant":
        voice_assistant_page(api_key)
    elif page == "📊 Analytics":
        analytics_page()
    elif page == "⚙️ Settings":
        settings_page()

def dashboard_page():
    """Main dashboard with overview metrics"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Quick Overview")
        
        # Load and display summary data
        df = st.session_state.agent.load_invoice_data()
        
        if not df.empty:
            # Summary metrics
            total_overdue = df[df['status'] == 'overdue']['invoice_amount'].sum()
            overdue_count = len(df[df['status'] == 'overdue'])
            avg_days_overdue = df[df['status'] == 'overdue']['days_overdue'].mean()
            
            # Metric cards
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("💸 Total Overdue", f"${total_overdue:,.2f}")
            with metric_col2:
                st.metric("📄 Overdue Count", overdue_count)
            with metric_col3:
                st.metric("⏰ Avg Days Overdue", f"{avg_days_overdue:.0f}")
            
            # Recent activity
            st.subheader("🔥 Most Urgent Invoices")
            urgent = df[df['status'] == 'overdue'].nlargest(5, 'days_overdue')[
                ['customer_name', 'invoice_amount', 'days_overdue']
            ]
            st.dataframe(urgent, use_container_width=True)
        
        else:
            st.error("❌ No invoice data found")
    
    with col2:
        st.header("🎯 Quick Actions")
        
        if st.button("🤖 Generate AI Follow-ups", type="primary", use_container_width=True):
            st.switch_page("🤖 AI Follow-ups")
        
        if st.button("🎤 Voice Commands", use_container_width=True):
            st.switch_page("🎤 Voice Assistant")
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.switch_page("📊 Analytics")
        
        st.markdown("---")
        st.markdown("### 💡 Pro Tips")
        st.info("💬 Try voice commands like:\n- 'List top 5 overdue invoices'\n- 'Generate reminders'\n- 'Customer insights for Tech Solutions'")

def ai_followups_page(api_key):
    """AI-powered follow-up generation page"""
    
    st.header("🤖 AI-Generated Follow-ups")
    
    # Configuration
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("⚙️ Configuration")
        
        num_followups = st.slider(
            "Number of Follow-ups",
            min_value=1,
            max_value=10,
            value=5
        )
        
        # Priority filters
        st.subheader("🔍 Filters")
        
        min_amount = st.number_input("Minimum Amount ($)", min_value=0, value=0)
        min_days = st.number_input("Minimum Days Overdue", min_value=0, value=0)
        
        industries = st.session_state.agent.load_invoice_data()['industry'].unique() if not st.session_state.agent.load_invoice_data().empty else []
        selected_industries = st.multiselect("Industries", industries, default=industries)
    
    with col2:
        if st.button("Generate Follow-up Emails", type="primary"):
            if not api_key:
                st.error("⚠️ Please provide your OpenAI API key in the sidebar.")
            else:
                with st.spinner("🔄 Generating personalized follow-up emails..."):
                    try:
                        followups = st.session_state.agent.generate_batch_followups(num_followups)
                        
                        # Apply filters
                        if min_amount > 0:
                            followups = [f for f in followups if f['amount'] >= min_amount]
                        if min_days > 0:
                            followups = [f for f in followups if f['days_overdue'] >= min_days]
                        
                        if followups:
                            st.success(f"✅ Generated {len(followups)} follow-up emails!")
                            
                            # Display results (same as before but in this page)
                            display_followup_results(followups)
                        else:
                            st.warning("⚠️ No invoices match your criteria.")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating follow-ups: {str(e)}")

def voice_assistant_page(api_key):
    """Voice assistant interface"""
    
    st.header("🎤 Voice Assistant")
    
    if not api_key:
        st.warning("⚠️ Please configure your OpenAI API key in the sidebar to use voice features.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🗣️ Voice Commands")
        
        # Text input for voice simulation
        voice_input = st.text_area(
            "Enter voice command (or speak):",
            placeholder="Try: 'List top 5 overdue invoices' or 'Generate 3 payment reminders'",
            height=100
        )
        
        if st.button("🎯 Process Command", type="primary"):
            if voice_input.strip():
                with st.spinner("🤖 Processing your request..."):
                    result = st.session_state.voice_agent.process_voice_command(voice_input)
                    
                    st.subheader("🤖 Assistant Response:")
                    st.write(result["response"])
                    
                    # Display data if available
                    if result["data"]:
                        st.subheader("📊 Data:")
                        if isinstance(result["data"], list) and len(result["data"]) > 0:
                            st.json(result["data"])
                        elif isinstance(result["data"], dict):
                            st.json(result["data"])
    
    with col2:
        st.subheader("💡 Voice Command Examples")
        
        examples = [
            "📋 List top 5 overdue invoices",
            "✉️ Generate 3 payment reminders", 
            "👤 Customer insights for Tech Solutions",
            "💰 What's our payment status?",
            "📊 Show overdue summary"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example}"):
                # Auto-fill the text area
                st.session_state.voice_input = example.split(" ", 1)[1]
                st.rerun()
        
        st.markdown("---")
        st.info("💭 **Coming Soon:** Real voice recognition with microphone input!")

def analytics_page():
    """Analytics dashboard page"""
    
    # Import analytics function
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from analytics_dashboard import create_analytics_dashboard
    
    create_analytics_dashboard()

def settings_page():
    """Settings and configuration page"""
    
    st.header("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Business Rules")
        
        # Overdue thresholds
        st.write("**Overdue Classification Thresholds:**")
        polite_days = st.number_input("Polite Reminder (days)", value=Config.OVERDUE_THRESHOLD_DAYS)
        firm_days = st.number_input("Firm Reminder (days)", value=Config.FIRM_REMINDER_DAYS)
        legal_days = st.number_input("Legal Escalation (days)", value=Config.LEGAL_ESCALATION_DAYS)
        
        # AI Model Settings
        st.write("**AI Model Configuration:**")
        model_choice = st.selectbox(
            "OpenAI Model",
            ["gpt-4", "gpt-3.5-turbo"],
            index=0 if Config.OPENAI_MODEL == "gpt-4" else 1
        )
        
        temperature = st.slider("AI Creativity (Temperature)", 0.0, 1.0, 0.7, 0.1)
        
        if st.button("💾 Save Business Rules"):
            # Update config (in a real app, this would persist to database)
            st.success("✅ Settings saved!")
    
    with col2:
        st.subheader("📊 Data Management")
        
        # Data refresh
        if st.button("🔄 Refresh Invoice Data"):
            # Clear cache and reload
            st.cache_data.clear()
            st.success("✅ Data refreshed!")
        
        # RAG Index Management
        st.write("**Knowledge Base:**")
        if st.button("🧠 Rebuild AI Knowledge Base"):
            with st.spinner("Rebuilding RAG index..."):
                st.session_state.agent.rag_engine.build_vector_index()
                st.session_state.agent.rag_engine.save_index()
                st.success("✅ Knowledge base rebuilt!")
        
        # Export options
        st.write("**Data Export:**")
        if st.button("📥 Export Invoice Data"):
            df = st.session_state.agent.load_invoice_data()
            csv = df.to_csv(index=False)
            st.download_button(
                "💾 Download CSV",
                csv,
                "invoice_data.csv",
                "text/csv"
            )
        
        # System info
        st.subheader("ℹ️ System Info")
        st.info(f"**Version:** {Config.VERSION}\n**Model:** {Config.OPENAI_MODEL}")

def display_followup_results(followups):
    """Display follow-up email results with enhanced UI"""
    
    for i, followup in enumerate(followups, 1):
        with st.expander(f"📧 {followup['customer_name']} - ${followup['amount']:,.2f} ({followup['days_overdue']} days overdue)", expanded=(i==1)):
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["📨 Generated Email", "🧠 AI Insights", "📊 Similar Cases"])
            
            with tab1:
                # Severity badge
                severity_colors = {
                    'polite': '🟢',
                    'firm': '🟡', 
                    'legal_escalation': '🔴'
                }
                col_sev, col_pri, col_follow = st.columns(3)
                with col_sev:
                    st.write(f"**Severity:** {severity_colors[followup['severity']]} {followup['severity'].replace('_', ' ').title()}")
                with col_pri:
                    st.write(f"**Priority Score:** {followup['priority_score']:.0f}")
                with col_follow:
                    st.write(f"**Follow-up in:** {followup['recommended_follow_up_hours']}")
                
                st.write(f"**Email:** {followup['customer_email']}")
                
                st.markdown("**Generated Email:**")
                st.text_area(
                    f"Email content for {followup['customer_name']}",
                    followup['generated_email'],
                    height=200,
                    key=f"email_{i}"
                )
            
            with tab2:
                # AI Insights
                insights = followup.get('ai_insights', {})
                if insights:
                    st.subheader("🎯 Customer Intelligence")
                    
                    comm_profile = insights.get('communication_profile', {})
                    recommendations = insights.get('recommendations', {})
                    historical = insights.get('historical_context', {})
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Communication Profile:**")
                        st.write(f"• Response Speed: {comm_profile.get('response_speed', 'Unknown')}")
                        st.write(f"• Preferred Channel: {comm_profile.get('preferred_channel', 'Unknown')}")
                        st.write(f"• Payment Reliability: {comm_profile.get('payment_reliability', 'Unknown')}")
                        st.write(f"• Recent Mood: {comm_profile.get('recent_mood', 'Unknown')}")
                    
                    with col2:
                        st.markdown("**AI Recommendations:**")
                        st.write(f"• Best Tone: {recommendations.get('best_tone', 'Unknown')}")
                        st.write(f"• Follow-up Timing: {recommendations.get('follow_up_timing', 'Unknown')}")
                        
                        risk_color = "🟢" if recommendations.get('escalation_risk') == 'low' else "🔴"
                        st.write(f"• Escalation Risk: {risk_color} {recommendations.get('escalation_risk', 'Unknown')}")
                    
                    st.markdown("**Historical Performance:**")
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        st.metric("Total Interactions", historical.get('total_interactions', 0))
                    with col4:
                        st.metric("Success Rate", f"{historical.get('success_rate_percentage', 0)}%")
                    with col5:
                        st.write(f"**Last Contact:** {historical.get('last_contact', 'Unknown')}")
                else:
                    st.info("🔄 No historical data available for this customer yet.")
            
            with tab3:
                # Similar Cases
                similar_cases = followup.get('similar_cases', [])
                if similar_cases:
                    st.subheader("📚 Learning from Similar Cases")
                    
                    for j, case in enumerate(similar_cases, 1):
                        with st.container():
                            st.markdown(f"**Case {j} - {case['date']}**")
                            st.write(f"**Type:** {case['type']}")
                            st.write(f"**Content:** {case['content'][:150]}...")
                            
                            result_colors = {
                                'paid_full': '🟢',
                                'paid_partial': '🟡',
                                'no_response': '🔴',
                                'payment_plan': '🟠'
                            }
                            result_color = result_colors.get(case['payment_result'], '⚪')
                            st.write(f"**Result:** {result_color} {case['payment_result'].replace('_', ' ').title()}")
                            st.write(f"**Similarity Score:** {case['similarity_score']:.2f}")
                            st.divider()
                else:
                    st.info("🔍 No similar cases found in the database.")
            
            # Action buttons
            st.markdown("---")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button(f"✅ Approve", key=f"approve_{i}"):
                    st.success("Email approved for sending!")
            with col_b:
                if st.button(f"✏️ Edit", key=f"edit_{i}"):
                    st.info("Edit functionality: Coming in next update!")
            with col_c:
                if st.button(f"📤 Send", key=f"send_{i}"):
                    st.success("Email sent! (Demo mode)")
            with col_d:
                if st.button(f"⏰ Schedule", key=f"schedule_{i}"):
                    st.info(f"Scheduled for follow-up in {followup['recommended_follow_up_hours']}")

if __name__ == "__main__":
    main()
    import streamlit as st
import pandas as pd
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.invoice_followup_agent import InvoiceFollowupAgent
from config import Config

def main():
    st.set_page_config(
        page_title="Finance AI Co-Pilot",
        page_icon="💰",
        layout="wide"
    )
    
    # Header
    st.title("💰 Finance AI Co-Pilot")
    st.subheader("Intelligent Invoice Follow-up Agent")
    st.markdown("---")
    
    # Initialize agent
    if 'agent' not in st.session_state:
        st.session_state.agent = InvoiceFollowupAgent()
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password",
        help="Enter your OpenAI API key to enable AI-powered email generation"
    )
    
    if api_key:
        Config.OPENAI_API_KEY = api_key
        st.sidebar.success("✅ API Key configured")
    
    # Number of follow-ups to generate
    num_followups = st.sidebar.slider(
        "Number of Follow-ups",
        min_value=1,
        max_value=10,
        value=5
    )
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📊 Invoice Overview")
        
        # Load and display invoice data
        df = st.session_state.agent.load_invoice_data()
        
        if not df.empty:
            # Summary metrics
            total_overdue = df[df['status'] == 'overdue']['invoice_amount'].sum()
            overdue_count = len(df[df['status'] == 'overdue'])
            avg_days_overdue = df[df['status'] == 'overdue']['days_overdue'].mean()
            
            st.metric("💸 Total Overdue", f"${total_overdue:,.2f}")
            st.metric("📄 Overdue Invoices", overdue_count)
            st.metric("⏰ Avg Days Overdue", f"{avg_days_overdue:.0f} days")
            
            # Show overdue invoices table
            st.subheader("Overdue Invoices")
            overdue_df = df[df['status'] == 'overdue'][
                ['invoice_id', 'customer_name', 'invoice_amount', 'days_overdue']
            ]
            st.dataframe(overdue_df, use_container_width=True)
        
        else:
            st.error("❌ No invoice data found. Please check your data files.")
    
    with col2:
        st.header("🤖 AI-Generated Follow-ups")
        
        if st.button("Generate Follow-up Emails", type="primary"):
            if not api_key:
                st.error("⚠️ Please provide your OpenAI API key in the sidebar.")
            else:
                with st.spinner("🔄 Generating personalized follow-up emails..."):
                    try:
                        followups = st.session_state.agent.generate_batch_followups(num_followups)
                        
                        if followups:
                            st.success(f"✅ Generated {len(followups)} follow-up emails!")
                            
                            # Display each follow-up
                            for i, followup in enumerate(followups, 1):
                                with st.expander(f"📧 {followup['customer_name']} - ${followup['amount']:,.2f} ({followup['days_overdue']} days overdue)", expanded=(i==1)):
                                    
                                    # Create tabs for different sections
                                    tab1, tab2, tab3 = st.tabs(["📨 Generated Email", "🧠 AI Insights", "📊 Similar Cases"])
                                    
                                    with tab1:
                                        # Severity badge
                                        severity_colors = {
                                            'polite': '🟢',
                                            'firm': '🟡', 
                                            'legal_escalation': '🔴'
                                        }
                                        col_sev, col_pri, col_follow = st.columns(3)
                                        with col_sev:
                                            st.write(f"**Severity:** {severity_colors[followup['severity']]} {followup['severity'].replace('_', ' ').title()}")
                                        with col_pri:
                                            st.write(f"**Priority Score:** {followup['priority_score']:.0f}")
                                        with col_follow:
                                            st.write(f"**Follow-up in:** {followup['recommended_follow_up_hours']}")
                                        
                                        st.write(f"**Email:** {followup['customer_email']}")
                                        
                                        st.markdown("**Generated Email:**")
                                        st.text_area(
                                            f"Email content for {followup['customer_name']}",
                                            followup['generated_email'],
                                            height=200,
                                            key=f"email_{i}"
                                        )
                                    
                                    with tab2:
                                        # AI Insights
                                        insights = followup.get('ai_insights', {})
                                        if insights:
                                            st.subheader("🎯 Customer Intelligence")
                                            
                                            comm_profile = insights.get('communication_profile', {})
                                            recommendations = insights.get('recommendations', {})
                                            historical = insights.get('historical_context', {})
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("**Communication Profile:**")
                                                st.write(f"• Response Speed: {comm_profile.get('response_speed', 'Unknown')}")
                                                st.write(f"• Preferred Channel: {comm_profile.get('preferred_channel', 'Unknown')}")
                                                st.write(f"• Payment Reliability: {comm_profile.get('payment_reliability', 'Unknown')}")
                                                st.write(f"• Recent Mood: {comm_profile.get('recent_mood', 'Unknown')}")
                                            
                                            with col2:
                                                st.markdown("**AI Recommendations:**")
                                                st.write(f"• Best Tone: {recommendations.get('best_tone', 'Unknown')}")
                                                st.write(f"• Follow-up Timing: {recommendations.get('follow_up_timing', 'Unknown')}")
                                                
                                                risk_color = "🟢" if recommendations.get('escalation_risk') == 'low' else "🔴"
                                                st.write(f"• Escalation Risk: {risk_color} {recommendations.get('escalation_risk', 'Unknown')}")
                                            
                                            st.markdown("**Historical Performance:**")
                                            col3, col4, col5 = st.columns(3)
                                            with col3:
                                                st.metric("Total Interactions", historical.get('total_interactions', 0))
                                            with col4:
                                                st.metric("Success Rate", f"{historical.get('success_rate_percentage', 0)}%")
                                            with col5:
                                                st.write(f"**Last Contact:** {historical.get('last_contact', 'Unknown')}")
                                        else:
                                            st.info("🔄 No historical data available for this customer yet.")
                                    
                                    with tab3:
                                        # Similar Cases
                                        similar_cases = followup.get('similar_cases', [])
                                        if similar_cases:
                                            st.subheader("📚 Learning from Similar Cases")
                                            
                                            for j, case in enumerate(similar_cases, 1):
                                                with st.container():
                                                    st.markdown(f"**Case {j} - {case['date']}**")
                                                    st.write(f"**Type:** {case['type']}")
                                                    st.write(f"**Content:** {case['content'][:150]}...")
                                                    
                                                    result_colors = {
                                                        'paid_full': '🟢',
                                                        'paid_partial': '🟡',
                                                        'no_response': '🔴',
                                                        'payment_plan': '🟠'
                                                    }
                                                    result_color = result_colors.get(case['payment_result'], '⚪')
                                                    st.write(f"**Result:** {result_color} {case['payment_result'].replace('_', ' ').title()}")
                                                    st.write(f"**Similarity Score:** {case['similarity_score']:.2f}")
                                                    st.divider()
                                        else:
                                            st.info("🔍 No similar cases found in the database.")
                                    
                                    # Action buttons
                                    st.markdown("---")
                                    col_a, col_b, col_c, col_d = st.columns(4)
                                    with col_a:
                                        if st.button(f"✅ Approve", key=f"approve_{i}"):
                                            st.success("Email approved for sending!")
                                    with col_b:
                                        if st.button(f"✏️ Edit", key=f"edit_{i}"):
                                            st.info("Edit functionality: Coming in next update!")
                                    with col_c:
                                        if st.button(f"📤 Send", key=f"send_{i}"):
                                            st.success("Email sent! (Demo mode)")
                                    with col_d:
                                        if st.button(f"⏰ Schedule", key=f"schedule_{i}"):
                                            st.info(f"Scheduled for follow-up in {followup['recommended_follow_up_hours']}")
                        else:
                            st.warning("⚠️ No overdue invoices found to follow up on.")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating follow-ups: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>Finance AI Co-Pilot v0.1.0 | Built for Peakflo</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()