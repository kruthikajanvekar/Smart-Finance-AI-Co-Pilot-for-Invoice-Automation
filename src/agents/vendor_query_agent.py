
import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Optional
import json
import re
from datetime import datetime, timedelta
from config import Config
import logging
import base64
import requests
from PIL import Image
import io
import pytesseract  # OCR library

class VendorQueryAgent:
    """AI-powered assistant to handle vendor queries automatically"""
    
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.logger = logging.getLogger(__name__)
        
        # Load vendor and payment data
        self.vendor_data = self._load_vendor_data()
        self.payment_data = self._load_payment_data()
        self.po_data = self._load_po_data()
    
    def _load_vendor_data(self) -> pd.DataFrame:
        """Load vendor information"""
        try:
            return pd.read_csv('data/vendor_master.csv')