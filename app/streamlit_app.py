
import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path to find src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
        "GEMINI API Key", 
        type="password",
        help="Enter your GEMINI API key to enable AI-powered email generation"
    )
    
    if api_key:
        Config.GOOGLE_API_KEY = api_key
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
                st.error("⚠️ Please provide your Google API key in the sidebar.")
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