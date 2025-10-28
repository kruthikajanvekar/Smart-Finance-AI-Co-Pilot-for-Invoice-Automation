# Save this as: src/agents/voice_agent.py

import google.generativeai as genai
import json
from typing import Dict, List, Optional
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import Config
import re

class VoiceFinanceAgent:
    def __init__(self, invoice_agent):
        self.invoice_agent = invoice_agent
        # API key configured in config.py_API_KEY
        
    def process_voice_command(self, transcript: str) -> Dict:
        """Process voice command and route to appropriate action"""
        
        # Intent classification
        intent = self._classify_intent(transcript)
        
        if intent == "list_overdue":
            return self._handle_list_overdue(transcript)
        elif intent == "generate_reminders":
            return self._handle_generate_reminders(transcript)
        elif intent == "customer_insights":
            return self._handle_customer_insights(transcript)
        elif intent == "payment_status":
            return self._handle_payment_status(transcript)
        else:
            return {
                "action": "unknown",
                "response": "I didn't understand that request. Try saying something like 'List top 5 overdue invoices' or 'Generate reminders for overdue payments'",
                "data": None
            }
    
    def _classify_intent(self, transcript: str) -> str:
        """Classify voice command intent using LLM"""
        
        prompt = f"""
        Classify the following finance-related voice command into one of these categories:
        
        Categories:
        - list_overdue: Commands to list, show, or display overdue invoices
        - generate_reminders: Commands to create, generate, or draft payment reminders
        - customer_insights: Commands to get customer information, history, or insights
        - payment_status: Commands to check payment status or when payments are due
        - unknown: Anything that doesn't fit the above categories
        
        Voice command: "{transcript}"
        
        Respond with only the category name.
        """
        
        try:
            response = genai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0
            )
            
            intent = response.choices[0].message.content.strip().lower()
            return intent if intent in ["list_overdue", "generate_reminders", "customer_insights", "payment_status"] else "unknown"
            
        except Exception as e:
            print(f"Error classifying intent: {e}")
            return "unknown"
    
    def _handle_list_overdue(self, transcript: str) -> Dict:
        """Handle requests to list overdue invoices"""
        
        # Extract number from transcript
        numbers = re.findall(r'\d+', transcript)
        limit = int(numbers[0]) if numbers else 5
        limit = min(limit, 10)  # Cap at 10
        
        df = self.invoice_agent.load_invoice_data()
        if df.empty:
            return {
                "action": "list_overdue",
                "response": "No invoice data available",
                "data": None
            }
        
        overdue_df = df[df['status'] == 'overdue']
        prioritized_df = self.invoice_agent.prioritize_followups(overdue_df)
        top_invoices = prioritized_df.head(limit)
        
        # Format response
        if len(top_invoices) == 0:
            response_text = "Great news! No overdue invoices found."
        else:
            response_text = f"Here are the top {len(top_invoices)} overdue invoices:\n\n"
            
            for i, (_, invoice) in enumerate(top_invoices.iterrows(), 1):
                response_text += f"{i}. {invoice['customer_name']}: ${invoice['invoice_amount']:,.2f}, {invoice['days_overdue']} days overdue\n"
        
        return {
            "action": "list_overdue",
            "response": response_text,
            "data": top_invoices.to_dict('records') if not top_invoices.empty else []
        }
    
    def _handle_generate_reminders(self, transcript: str) -> Dict:
        """Handle requests to generate payment reminders"""
        
        # Extract number from transcript
        numbers = re.findall(r'\d+', transcript)
        limit = int(numbers[0]) if numbers else 3
        limit = min(limit, 5)  # Cap at 5 for voice
        
        try:
            followups = self.invoice_agent.generate_batch_followups(limit)
            
            if not followups:
                return {
                    "action": "generate_reminders",
                    "response": "No overdue invoices require follow-up at this time.",
                    "data": []
                }
            
            response_text = f"I've generated {len(followups)} personalized payment reminders:\n\n"
            
            for i, followup in enumerate(followups, 1):
                severity_desc = {
                    'polite': 'friendly',
                    'firm': 'direct',
                    'legal_escalation': 'urgent'
                }
                
                response_text += f"{i}. {followup['customer_name']}: {severity_desc.get(followup['severity'], 'standard')} reminder for ${followup['amount']:,.2f}\n"
            
            response_text += "\nAll reminders are ready for review in the dashboard."
            
            return {
                "action": "generate_reminders", 
                "response": response_text,
                "data": followups
            }
            
        except Exception as e:
            return {
                "action": "generate_reminders",
                "response": f"Error generating reminders: {str(e)}",
                "data": []
            }
    
    def _handle_customer_insights(self, transcript: str) -> Dict:
        """Handle requests for customer insights"""
        
        # Try to extract customer name from transcript
        customer_name = self._extract_customer_name(transcript)
        
        if not customer_name:
            return {
                "action": "customer_insights",
                "response": "Please specify which customer you'd like insights for.",
                "data": None
            }
        
        # Find customer in data
        df = self.invoice_agent.load_invoice_data()
        customer_row = df[df['customer_name'].str.contains(customer_name, case=False, na=False)]
        
        if customer_row.empty:
            return {
                "action": "customer_insights",
                "response": f"Customer '{customer_name}' not found in the database.",
                "data": None
            }
        
        customer_data = customer_row.iloc[0]
        customer_id = customer_data['customer_id']
        
        # Get insights from RAG engine
        insights = self.invoice_agent.rag_engine.get_customer_insights(customer_id)
        
        if not insights:
            response_text = f"Limited data available for {customer_data['customer_name']}. Current invoice: ${customer_data['invoice_amount']:,.2f}, {customer_data['days_overdue']} days overdue."
        else:
            comm_profile = insights['communication_profile']
            recommendations = insights['recommendations']
            historical = insights['historical_context']
            
            response_text = f"""Here are insights for {customer_data['customer_name']}:
            
• Payment reliability: {comm_profile['payment_reliability']}
• Typical response time: {comm_profile['response_speed']}
• Success rate: {historical['success_rate_percentage']}%
• Recommended approach: Use a {recommendations['best_tone']} tone
• Follow up in: {recommendations['follow_up_timing']}
• Risk level: {recommendations['escalation_risk']}"""
        
        return {
            "action": "customer_insights",
            "response": response_text,
            "data": {
                "customer_data": customer_data.to_dict(),
                "insights": insights
            }
        }
    
    def _handle_payment_status(self, transcript: str) -> Dict:
        """Handle payment status inquiries"""
        
        df = self.invoice_agent.load_invoice_data()
        
        # Summary statistics
        total_outstanding = df[df['status'] == 'overdue']['invoice_amount'].sum()
        overdue_count = len(df[df['status'] == 'overdue'])
        
        if overdue_count == 0:
            response_text = "Excellent! All invoices are current with no overdue payments."
        else:
            avg_days_overdue = df[df['status'] == 'overdue']['days_overdue'].mean()
            
            response_text = f"""Current payment status summary:
            
• Total outstanding: ${total_outstanding:,.2f}
• Number of overdue invoices: {overdue_count}
• Average days overdue: {avg_days_overdue:.0f} days

The most urgent invoice is {df.loc[df['days_overdue'].idxmax(), 'customer_name']} at {df['days_overdue'].max()} days overdue."""
        
        return {
            "action": "payment_status",
            "response": response_text,
            "data": {
                "total_outstanding": total_outstanding,
                "overdue_count": overdue_count,
                "avg_days_overdue": df[df['status'] == 'overdue']['days_overdue'].mean() if overdue_count > 0 else 0
            }
        }
    
    def _extract_customer_name(self, transcript: str) -> Optional[str]:
        """Extract customer name from transcript using LLM"""
        
        prompt = f"""
        Extract the customer/company name from this voice command about finance operations.
        If no specific customer name is mentioned, return "NONE".
        
        Voice command: "{transcript}"
        
        Customer name (or NONE):
        """
        
        try:
            response = genai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            return None if result.upper() == "NONE" else result
            
        except Exception as e:
            print(f"Error extracting customer name: {e}")
            return None
    
    def format_for_speech(self, response_data: Dict) -> str:
        """Format response for text-to-speech output"""
        
        # Clean up text for better speech synthesis
        text = response_data["response"]
        
        # Replace symbols with words
        text = re.sub(r'\$', 'dollar ', text)
        text = re.sub(r'&', ' and ', text)
        text = re.sub(r'%', ' percent', text)
        text = re.sub(r'#', ' number ', text)
        
        # Add pauses for better speech flow
        text = re.sub(r'\n\n', '. ', text)
        text = re.sub(r'\n', ', ', text)
        text = re.sub(r'•', '. ', text)
        
        return text