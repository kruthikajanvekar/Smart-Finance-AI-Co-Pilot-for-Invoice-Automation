import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GOOGLE_API_KEY)

class InvoiceFollowupAgent:
    def __init__(self):
        # API key configured in config.py
        self.config = Config()
        
    def load_invoice_data(self) -> pd.DataFrame:
        """Load invoice data from CSV file"""
        try:
            return pd.read_csv(Config.SAMPLE_INVOICES_PATH)
        except Exception as e:
            print(f"Error loading invoice data: {e}")
            return pd.DataFrame()
    
    def categorize_overdue_severity(self, days_overdue: int) -> str:
        """Categorize invoice based on how overdue it is"""
        if days_overdue <= Config.OVERDUE_THRESHOLD_DAYS:
            return "polite"
        elif days_overdue <= Config.FIRM_REMINDER_DAYS:
            return "firm"
        else:
            return "legal_escalation"
    
    def get_customer_context(self, customer_data: Dict) -> str:
        """Generate customer context for personalized communication"""
        context = f"""
        Customer: {customer_data['customer_name']}
        Industry: {customer_data['industry']}
        Relationship Length: {customer_data['relationship_length_months']} months
        Payment History Score: {customer_data['payment_history_score']}/10
        Last Payment: {customer_data['last_payment_date']}
        Invoice Amount: ${customer_data['invoice_amount']:,.2f}
        Days Overdue: {customer_data['days_overdue']}
        """
        return context
    
    def generate_followup_email(self, invoice_data: Dict) -> str:
        """Generate personalized follow-up email using LLM"""
        
        severity = self.categorize_overdue_severity(invoice_data['days_overdue'])
        customer_context = self.get_customer_context(invoice_data)
        
        # Dynamic prompt based on severity and customer context
        if severity == "polite":
            tone = "friendly and professional"
            urgency = "gentle reminder"
        elif severity == "firm":
            tone = "professional but more direct"
            urgency = "firm but respectful follow-up"
        else:
            tone = "formal and serious"
            urgency = "final notice before escalation"
        
        prompt = f"""
        You are a Finance AI Assistant helping to draft a personalized invoice follow-up email.
        
        Customer Context:
        {customer_context}
        
        Task: Write a {tone} email for a {urgency} about the overdue invoice.
        
        Guidelines:
        1. Be {tone}
        2. Reference their payment history appropriately (good history = more lenient, poor history = more direct)
        3. Mention the specific invoice amount and overdue period
        4. Include a clear call-to-action
        5. Keep it concise (under 200 words)
        6. Use proper business email format
        
        Email Subject: Payment Reminder - Invoice {invoice_data['invoice_id']}
        
        Generate the email body:
        """
        
        try:
            response = genai.chat.create(
                model=Config.GEMINI_MODEL,
                messages=[
                    {"author": "system", "content": "You are a professional finance communication specialist."},
                    {"author": "user", "content": prompt}
                    ],
                temperature=0.7,
                max_output_tokens=300,
                )
            return response.last

            # return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating email: {str(e)}"
    
    def prioritize_followups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prioritize follow-ups based on amount, days overdue, and payment history"""
        
        # Calculate priority score
        df['priority_score'] = (
            df['invoice_amount'] * 0.4 +  # 40% weight on amount
            df['days_overdue'] * 100 * 0.4 +  # 40% weight on overdue days
            (10 - df['payment_history_score']) * 1000 * 0.2  # 20% weight on payment history (inverted)
        )
        
        return df.sort_values('priority_score', ascending=False)
    
    def generate_batch_followups(self, limit: int = 5) -> List[Dict]:
        """Generate follow-up emails for top priority invoices"""
        
        df = self.load_invoice_data()
        if df.empty:
            return []
        
        # Filter only overdue invoices
        overdue_df = df[df['status'] == 'overdue']
        
        # Prioritize
        prioritized_df = self.prioritize_followups(overdue_df)
        
        # Take top N
        top_invoices = prioritized_df.head(limit)
        
        results = []
        for _, invoice in top_invoices.iterrows():
            email_content = self.generate_followup_email(invoice.to_dict())
            
            results.append({
                'invoice_id': invoice['invoice_id'],
                'customer_name': invoice['customer_name'],
                'customer_email': invoice['customer_email'],
                'amount': invoice['invoice_amount'],
                'days_overdue': invoice['days_overdue'],
                'severity': self.categorize_overdue_severity(invoice['days_overdue']),
                'priority_score': invoice['priority_score'],
                'generated_email': email_content
            })
        
        return results