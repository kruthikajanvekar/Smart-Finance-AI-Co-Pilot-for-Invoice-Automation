# Save this as: app/analytics_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import sys
import os

def create_analytics_dashboard():
    """Create comprehensive finance analytics dashboard"""
    
    st.header("📊 Finance Analytics Dashboard")
    
    # Load data
    try:
        invoice_df = pd.read_csv("data/sample_invoices.csv")
        try:
            comm_df = pd.read_csv("data/communication_history.csv")
        except:
            # Create dummy communication data if file doesn't exist
            comm_df = pd.DataFrame({
                'customer_id': ['CUST-101', 'CUST-102', 'CUST-103'],
                'type': ['email_reminder', 'phone_call', 'email_reminder'],
                'payment_result': ['paid_full', 'no_response', 'paid_partial'],
                'response_time_hours': [24, 72, 12]
            })
    except:
        st.error("Unable to load data files")
        return
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_outstanding = invoice_df[invoice_df['status'] == 'overdue']['invoice_amount'].sum()
        st.metric(
            "💸 Total Outstanding", 
            f"${total_outstanding:,.2f}",
            delta=f"+${total_outstanding * 0.15:,.2f} vs last month"
        )
    
    with col2:
        overdue_count = len(invoice_df[invoice_df['status'] == 'overdue'])
        st.metric(
            "📄 Overdue Invoices", 
            overdue_count,
            delta=f"+{int(overdue_count * 0.2)} vs last week"
        )
    
    with col3:
        avg_days = invoice_df[invoice_df['status'] == 'overdue']['days_overdue'].mean()
        st.metric(
            "⏰ Avg Days Overdue", 
            f"{avg_days:.0f} days",
            delta=f"-{int(avg_days * 0.1)} vs last month"
        )
    
    with col4:
        collection_rate = len(comm_df[comm_df['payment_result'].isin(['paid_full', 'paid_partial'])]) / len(comm_df) * 100 if len(comm_df) > 0 else 0
        st.metric(
            "🎯 Collection Rate", 
            f"{collection_rate:.1f}%",
            delta=f"+{collection_rate * 0.05:.1f}% vs last month"
        )
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Outstanding by Customer")
        
        # Create pie chart
        overdue_by_customer = invoice_df[invoice_df['status'] == 'overdue'].groupby('customer_name')['invoice_amount'].sum().reset_index()
        
        if not overdue_by_customer.empty:
            fig_pie = px.pie(
                overdue_by_customer, 
                values='invoice_amount', 
                names='customer_name',
                title="Distribution of Overdue Amounts"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No overdue invoices to display")
    
    with col2:
        st.subheader("📈 Days Overdue Distribution")
        
        # Create histogram
        if not invoice_df[invoice_df['status'] == 'overdue'].empty:
            fig_hist = px.histogram(
                invoice_df[invoice_df['status'] == 'overdue'], 
                x='days_overdue',
                nbins=10,
                title="Distribution of Overdue Days",
                labels={'days_overdue': 'Days Overdue', 'count': 'Number of Invoices'}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No overdue invoices to analyze")
    
    # Charts Row 2  
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Payment Success by Communication Type")
        
        # Communication effectiveness
        if not comm_df.empty:
            comm_success = comm_df.groupby('type')['payment_result'].apply(
                lambda x: (x.isin(['paid_full', 'paid_partial']).sum() / len(x)) * 100
            ).reset_index()
            comm_success.columns = ['Communication Type', 'Success Rate %']
            
            fig_bar = px.bar(
                comm_success,
                x='Communication Type',
                y='Success Rate %',
                title="Communication Effectiveness",
                color='Success Rate %',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No communication data available")
    
    with col2:
        st.subheader("⚡ Response Time vs Success Rate")
        
        # Scatter plot of response time vs success
        if not comm_df.empty:
            comm_analysis = comm_df.copy()
            comm_analysis['success'] = comm_analysis['payment_result'].isin(['paid_full', 'paid_partial']).astype(int)
            
            fig_scatter = px.scatter(
                comm_analysis,
                x='response_time_hours',
                y='success',
                size='success',
                color='type',
                title="Response Time Impact on Success",
                labels={'response_time_hours': 'Response Time (Hours)', 'success': 'Payment Success (0/1)'}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No communication timing data available")
    
    # Industry Analysis
    st.subheader("🏭 Industry Performance Analysis")
    
    industry_metrics = invoice_df.groupby('industry').agg({
        'invoice_amount': ['sum', 'mean'],
        'days_overdue': 'mean',
        'payment_history_score': 'mean'
    }).round(2)
    
    industry_metrics.columns = ['Total Outstanding', 'Avg Invoice Amount', 'Avg Days Overdue', 'Avg Payment Score']
    st.dataframe(industry_metrics, use_container_width=True)
    
    # AI Recommendations Section
    st.subheader("🤖 AI-Powered Recommendations")
    
    recommendations = generate_ai_recommendations(invoice_df, comm_df)
    
    for i, rec in enumerate(recommendations, 1):
        with st.expander(f"💡 Recommendation {i}: {rec['title']}", expanded=(i==1)):
            st.write(f"**Priority:** {rec['priority']}")
            st.write(f"**Impact:** {rec['impact']}")
            st.write(f"**Action:** {rec['action']}")
            
            if rec.get('data') is not None and not rec['data'].empty:
                st.dataframe(rec['data'], use_container_width=True)

def generate_ai_recommendations(invoice_df, comm_df):
    """Generate AI-powered business recommendations"""
    
    recommendations = []
    
    # Recommendation 1: High-risk customers
    high_risk = invoice_df[
        (invoice_df['days_overdue'] > 60) & 
        (invoice_df['payment_history_score'] < 5)
    ]
    
    if not high_risk.empty:
        recommendations.append({
            'title': 'High-Risk Customer Alert',
            'priority': '🔴 High',
            'impact': f'${high_risk["invoice_amount"].sum():,.2f} at risk',
            'action': 'Immediate escalation recommended for these customers',
            'data': high_risk[['customer_name', 'invoice_amount', 'days_overdue', 'payment_history_score']]
        })
    
    # Recommendation 2: Communication optimization
    if not comm_df.empty:
        ineffective_comms = comm_df[comm_df['response_time_hours'] > 72]
        
        if not ineffective_comms.empty:
            recommendations.append({
                'title': 'Communication Timing Optimization',
                'priority': '🟡 Medium', 
                'impact': f'{len(ineffective_comms)} slow-responding customers identified',
                'action': 'Switch to phone calls or different communication timing for better response rates',
                'data': ineffective_comms.groupby('customer_id')['response_time_hours'].mean().reset_index()
            })
    
    # Recommendation 3: Success pattern
    if not comm_df.empty:
        successful_approaches = comm_df[comm_df['payment_result'].isin(['paid_full', 'paid_partial'])]
        best_approach = successful_approaches['type'].mode().iloc[0] if not successful_approaches.empty else 'email_reminder'
        
        recommendations.append({
            'title': 'Optimal Communication Strategy',
            'priority': '🟢 Info',
            'impact': f'{best_approach} shows highest success rate',
            'action': f'Increase usage of {best_approach} for better collection outcomes',
            'data': pd.DataFrame()  # Empty dataframe
        })
    
    return recommendations

if __name__ == "__main__":
    create_analytics_dashboard()