"""
Utility functions used across the project
Helper functions for common operations
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

def format_currency(amount: float) -> str:
    """Format number as currency with commas"""
    return f"${amount:,.2f}"

def calculate_days_between(start_date: str, end_date: str) -> int:
    """Calculate days between two dates"""
    
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return (end - start).days
    except:
        return 0

def extract_invoice_number(text: str) -> Optional[str]:
    """Extract invoice number from text"""
    
    # Pattern: INV followed by numbers
    pattern = r'INV[#-]?(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return f"INV{match.group(1).zfill(3)}"
    return None

def extract_amount(text: str) -> Optional[float]:
    """Extract dollar amount from text"""
    
    # Pattern: $ followed by numbers
    pattern = r'\$?([\d,]+\.?\d*)'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            return float(amount_str)
        except:
            return None
    return None

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix"""
    
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def validate_email(email: str) -> bool:
    """Validate email format"""
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def parse_json_safe(json_str: str) -> Dict:
    """Safely parse JSON string"""
    
    try:
        return json.loads(json_str)
    except:
        return {}

def calculate_payment_date(invoice_date: str, payment_terms: str) -> str:
    """Calculate expected payment date based on terms"""
    
    try:
        invoice_dt = pd.to_datetime(invoice_date)
        
        # Extract days from terms (e.g., "Net 30" -> 30)
        days_match = re.search(r'\d+', payment_terms)
        days = int(days_match.group()) if days_match else 30
        
        payment_dt = invoice_dt + timedelta(days=days)
        return payment_dt.strftime('%Y-%m-%d')
        
    except:
        return ""

def get_business_days_between(start_date: str, end_date: str) -> int:
    """Calculate business days between two dates (excluding weekends)"""
    
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Use pandas business day calculation
        business_days = pd.bdate_range(start, end)
        return len(business_days)
        
    except:
        return 0

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

class DateHelper:
    """Helper class for date operations"""
    
    @staticmethod
    def is_weekend(date_str: str) -> bool:
        """Check if date falls on weekend"""
        try:
            dt = pd.to_datetime(date_str)
            return dt.weekday() >= 5  # 5=Saturday, 6=Sunday
        except:
            return False
    
    @staticmethod
    def is_business_hours(time_str: str) -> bool:
        """Check if time is during business hours (9 AM - 5 PM)"""
        try:
            dt = pd.to_datetime(time_str)
            hour = dt.hour
            return 9 <= hour < 17
        except:
            return True
    
    @staticmethod
    def format_relative_date(date_str: str) -> str:
        """Format date as relative time (e.g., '2 days ago')"""
        try:
            dt = pd.to_datetime(date_str)
            now = datetime.now()
            diff = now - dt
            
            if diff.days == 0:
                return "Today"
            elif diff.days == 1:
                return "Yesterday"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            elif diff.days < 30:
                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = diff.days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
        except:
            return date_str
