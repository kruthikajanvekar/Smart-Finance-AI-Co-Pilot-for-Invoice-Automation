
import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from config import Config
from src.logger.logger import get_logger
logger = get_logger(__name__)


genai.configure(api_key=Config.GOOGLE_API_KEY)

class VendorQueryAgent:
    """AI-powered assistant to handle vendor queries automatically"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.vendor_data = self._load_vendor_data()
        self.payment_data = self._load_payment_data()
        self.po_data = self._load_po_data()
    
    def _load_vendor_data(self) -> pd.DataFrame:
        try:
            return pd.read_csv('data/vendor_master.csv')
        except Exception as e:
            self.logger.error(f'Error loading vendor data: {e}')
            return pd.DataFrame()
    
    def _load_payment_data(self) -> pd.DataFrame:
        try:
            return pd.read_csv('data/vendor_invoices.csv')
        except Exception as e:
            self.logger.error(f'Error loading payment data: {e}')
            return pd.DataFrame()
    
    def _load_po_data(self) -> pd.DataFrame:
        try:
            return pd.read_csv('data/purchase_orders.csv')
        except Exception as e:
            self.logger.error(f'Error loading PO data: {e}')
            return pd.DataFrame()
    
    def process_vendor_query(self, query: str, vendor_email: str = None) -> Dict:
        try:
            # Quick check: ensure API key is configured before making LLM calls
            if not Config.GOOGLE_API_KEY:
                self.logger.warning('GOOGLE_API_KEY is not configured')
                return {
                    'query': query,
                    'response': 'AI service not configured. Please set `GOOGLE_API_KEY` in your environment or in the app sidebar.',
                    'vendor_email': vendor_email,
                    'vendor_id': None,
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                }

            # Find vendor by email if provided
            vendor_info = pd.DataFrame()
            vendor_id = None
            
            if vendor_email and not self.vendor_data.empty:
                vendor_matches = self.vendor_data[self.vendor_data['contact_email'] == vendor_email]
                if not vendor_matches.empty:
                    vendor_info = vendor_matches
                    vendor_id = vendor_matches.iloc[0]['vendor_id']
            
            # Get payment history for this vendor
            payments = self.payment_data[self.payment_data['vendor_id'] == vendor_id] if vendor_id and not self.payment_data.empty else pd.DataFrame()
            po_info = self.po_data[self.po_data['vendor_id'] == vendor_id] if vendor_id and not self.po_data.empty else pd.DataFrame()
            
            # Build context from data
            context = self._build_context(vendor_info, payments, po_info)
            
            # Generate AI response with clear instructions
            system_instruction = """You are a vendor support assistant. You have access to this vendor's account data.
Your role is to:
1. Answer questions ONLY based on the provided vendor account information
2. Be specific and factual - reference exact invoice numbers, amounts, and dates
3. If the vendor asks about pending invoices, list them explicitly
4. Keep responses concise and professional
5. If you don't have information about something, say so clearly

DO NOT give generic financial advice. Use the specific data provided."""

            prompt = f"""{system_instruction}

VENDOR ACCOUNT INFORMATION:
{context}

VENDOR QUESTION:
{query}

RESPONSE (be specific and reference actual invoices/amounts):"""
            
            # Attempt LLM call; if it fails (quota/network/etc.) fall back to local CSV summary
            try:
                response = self.model.generate_content(prompt)
            except Exception as llm_exc:
                self.logger.warning('LLM call failed, using local CSV fallback: %s', llm_exc)
                fallback_text = self._fallback_response(vendor_info, payments, po_info)
                return {
                    'query': query,
                    'response': fallback_text,
                    'vendor_email': vendor_email,
                    'vendor_id': vendor_id,
                    'success': True,
                    'generated_from': 'local_data_fallback',
                    'error': str(llm_exc),
                    'timestamp': datetime.now().isoformat()
                }

            # Robustly extract text from different response shapes
            response_text = ''
            try:
                if response is None:
                    response_text = 'Unable to generate response'
                elif hasattr(response, 'text'):
                    response_text = response.text
                elif isinstance(response, dict):
                    # google generative responses sometimes include candidates/content
                    if 'candidates' in response and response['candidates']:
                        response_text = response['candidates'][0].get('content', '')
                    else:
                        # fallback to stringifying the response
                        response_text = json.dumps(response)
                else:
                    response_text = str(response)
            except Exception as _ex:
                self.logger.debug('Error extracting text from LLM response: %s', _ex)
                response_text = 'Unable to parse LLM response'

            return {
                'query': query,
                'response': response_text,
                'vendor_email': vendor_email,
                'vendor_id': vendor_id,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f'Error processing vendor query: {e}')
            return {
                'query': query, 
                'response': f'Unable to process your query. Please try again later. (Error: {type(e).__name__})', 
                'error': str(e),
                'vendor_email': vendor_email if 'vendor_email' in locals() else None,
                'vendor_id': vendor_id if 'vendor_id' in locals() else None,
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_context(self, vendor_info: pd.DataFrame, payments: pd.DataFrame, po_info: pd.DataFrame = None) -> str:
        context = ""
        
        # Vendor Basic Info
        if not vendor_info.empty:
            vendor = vendor_info.iloc[0]
            context += f"VENDOR: {vendor.get('vendor_name', 'Unknown')}\n"
            context += f"Payment Terms: {vendor.get('payment_terms', 'N/A')}\n"
            context += f"Status: {vendor.get('status', 'N/A')}\n"
            context += f"Contact: {vendor.get('contact_email', 'N/A')}\n\n"
        
        # Pending Invoices (Most Important)
        if not payments.empty:
            context += f"PENDING INVOICES:\n"
            context += "-" * 60 + "\n"
            pending_count = 0
            total_pending = 0
            for idx, payment in payments.iterrows():
                invoice_id = payment.get('invoice_id', 'N/A')
                amount = float(payment.get('total_amount', 0))
                status = payment.get('status', 'N/A')
                invoice_date = payment.get('invoice_date', 'N/A')
                description = payment.get('description', 'N/A')
                
                context += f"\n• Invoice: {invoice_id}\n"
                context += f"  Amount: ${amount:,.2f}\n"
                context += f"  Date: {invoice_date}\n"
                context += f"  Description: {description}\n"
                context += f"  Status: {status}\n"
                
                if status.lower() == 'pending':
                    pending_count += 1
                    total_pending += amount
            
            context += "-" * 60 + "\n"
            context += f"Total Pending Amount: ${total_pending:,.2f}\n"
            context += f"Number of Pending Invoices: {pending_count}\n\n"
        else:
            context += "PENDING INVOICES: None\n\n"
        
        # PO Info
        if po_info is not None and not po_info.empty:
            context += f"RECENT PURCHASE ORDERS:\n"
            context += "-" * 60 + "\n"
            for idx, po in po_info.head(3).iterrows():
                po_number = po.get('po_number', 'N/A')
                amount = float(po.get('total_amount', 0))
                status = po.get('status', 'N/A')
                
                context += f"• PO: {po_number} | Amount: ${amount:,.2f} | Status: {status}\n"
            context += "-" * 60 + "\n\n"
        
        return context if context else "No vendor information available"

    def _fallback_response(self, vendor_info: pd.DataFrame, payments: pd.DataFrame, po_info: pd.DataFrame = None) -> str:
        """Build a deterministic, human-readable response from local CSV data.

        This is used when LLM calls fail (quota/network). It mirrors what
        vendors expect: a concise list of pending invoices and totals.
        """
        lines = []
        if not vendor_info.empty:
            vendor = vendor_info.iloc[0]
            lines.append(f"Vendor: {vendor.get('vendor_name', 'Unknown')}")
            lines.append(f"Contact: {vendor.get('contact_email', 'N/A')}")
            lines.append(f"Payment Terms: {vendor.get('payment_terms', 'N/A')}")
            lines.append("")

        if payments is None or payments.empty:
            lines.append("No invoices found for this account.")
            return "\n".join(lines)

        lines.append("Pending Invoices:")
        total_pending = 0.0
        count_pending = 0
        for idx, payment in payments.iterrows():
            invoice_id = payment.get('invoice_id', 'N/A')
            amount = float(payment.get('total_amount', 0) or 0)
            status = payment.get('status', 'N/A')
            invoice_date = payment.get('invoice_date', 'N/A')
            lines.append(f" - {invoice_id} | Amount: ${amount:,.2f} | Date: {invoice_date} | Status: {status}")
            if str(status).strip().lower() == 'pending':
                total_pending += amount
                count_pending += 1

        lines.append("")
        lines.append(f"Number of Pending Invoices: {count_pending}")
        lines.append(f"Total Pending Amount: ${total_pending:,.2f}")

        if po_info is not None and not po_info.empty:
            lines.append("")
            lines.append("Recent Purchase Orders:")
            for idx, po in po_info.head(3).iterrows():
                po_number = po.get('po_number', 'N/A')
                amount = float(po.get('total_amount', 0) or 0)
                status = po.get('status', 'N/A')
                lines.append(f" - {po_number} | Amount: ${amount:,.2f} | Status: {status}")

        lines.append("")
        lines.append("If you need more detail, contact our vendor support team or try again later.")
        return "\n".join(lines)
    
'''
with open('src/agents/vendor_query_agent.py', 'w') as f:
    f.write(vendor_agent_code)
print('✅ Fixed vendor_query_agent.py')
'''
