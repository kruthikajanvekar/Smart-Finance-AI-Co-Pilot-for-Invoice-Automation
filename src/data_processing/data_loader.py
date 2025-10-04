"""
Data loading utilities for invoice and customer data
Handles CSV, Excel, and database connections
"""

import pandas as pd
import os
from typing import Dict, List, Optional
import logging
from config import Config

class DataLoader:
    """Centralized data loading for all finance data sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_cache = {}  # Simple in-memory cache
    
    def load_invoices(self, use_cache: bool = True) -> pd.DataFrame:
        """Load invoice data with caching"""
        
        cache_key = 'invoices'
        
        # Check cache first
        if use_cache and cache_key in self.data_cache:
            self.logger.info("Loading invoices from cache")
            return self.data_cache[cache_key]
        
        # Load from file
        try:
            df = pd.read_csv(Config.SAMPLE_INVOICES_PATH)
            
            # Data cleaning
            df = self._clean_invoice_data(df)
            
            # Cache it
            self.data_cache[cache_key] = df
            
            self.logger.info(f"Loaded {len(df)} invoices from file")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading invoices: {e}")
            return pd.DataFrame()
    
    def load_customer_history(self) -> pd.DataFrame:
        """Load customer communication history"""
        
        try:
            history_path = os.path.join(Config.DATA_DIR, "communication_history.csv")
            df = pd.read_csv(history_path)
            return df
        except Exception as e:
            self.logger.error(f"Error loading customer history: {e}")
            return pd.DataFrame()
    
    def load_from_excel(self, filepath: str, sheet_name: str = 0) -> pd.DataFrame:
        """Load data from Excel file"""
        
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            self.logger.info(f"Loaded {len(df)} rows from Excel: {filepath}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading Excel file: {e}")
            return pd.DataFrame()
    
    def _clean_invoice_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate invoice data"""
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['invoice_id'], keep='last')
        
        # Fill missing values
        df['customer_email'] = df['customer_email'].fillna('no-email@example.com')
        df['payment_history_score'] = df['payment_history_score'].fillna(5.0)
        
        # Convert dates to datetime
        date_columns = ['issue_date', 'due_date', 'last_payment_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Ensure numeric columns
        numeric_columns = ['invoice_amount', 'days_overdue', 'payment_history_score']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def save_invoices(self, df: pd.DataFrame, filepath: Optional[str] = None) -> bool:
        """Save invoice data to CSV"""
        
        if filepath is None:
            filepath = Config.SAMPLE_INVOICES_PATH
        
        try:
            df.to_csv(filepath, index=False)
            self.logger.info(f"Saved {len(df)} invoices to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving invoices: {e}")
            return False
    
    def clear_cache(self):
        """Clear data cache"""
        self.data_cache.clear()
        self.logger.info("Data cache cleared")
