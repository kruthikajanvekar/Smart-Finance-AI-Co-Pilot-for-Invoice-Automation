
import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
from config import Config

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
    
    def process_vendor_query(self, query: str, vendor_id: str = None) -> Dict:
        try:
            vendor_info = self.vendor_data[self.vendor_data['vendor_id'] == vendor_id] if vendor_id and not self.vendor_data.empty else pd.DataFrame()
            payments = self.payment_data[self.payment_data['vendor_id'] == vendor_id] if vendor_id and not self.payment_data.empty else pd.DataFrame()
            context = self._build_context(vendor_info, payments)
            prompt = f'You are a helpful finance assistant. Query: {query}\\nContext: {context}'
            response = self.model.generate_content(prompt)
            return {'query': query, 'response': response.text if response.text else 'Unable to process', 'vendor_id': vendor_id, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            self.logger.error(f'Error: {e}')
            return {'query': query, 'response': 'Sorry, unable to process', 'error': str(e)}
    
    def _build_context(self, vendor_info: pd.DataFrame, payments: pd.DataFrame) -> str:
        context = ''
        if not vendor_info.empty:
            vendor = vendor_info.iloc[0]
            context += f"Vendor: {vendor.get('vendor_name', 'Unknown')}\n"
            context += f"Terms: {vendor.get('payment_terms', 'N/A')}\n"
        if not payments.empty:
            context += f'Recent Payments: {len(payments)}\\n'
        return context if context else 'No info'
    
'''
with open('src/agents/vendor_query_agent.py', 'w') as f:
    f.write(vendor_agent_code)
print('✅ Fixed vendor_query_agent.py')
'''
