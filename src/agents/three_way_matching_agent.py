import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import google.generativeai as genai
from config import Config
import json
import logging
from datetime import datetime
import difflib

class ThreeWayMatchingAgent:
    """AI-powered 3-way matching for Purchase Orders, Goods Receipt Notes, and Invoices"""
    
    def __init__(self):
        genai.api_key = Config.GENAI_API_KEY
        self.logger = logging.getLogger(__name__)
        self.tolerance_config = {
            'quantity_tolerance_percent': 5.0,  # 5% tolerance
            'price_tolerance_percent': 2.0,     # 2% tolerance  
            'total_tolerance_amount': 10.0      # $10 absolute tolerance
        }
    
    def load_matching_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load PO, GRN, and Invoice data for matching"""
        
        try:
            # Load sample data (in production, this would come from ERP)
            po_df = pd.read_csv('data/purchase_orders.csv')
            grn_df = pd.read_csv('data/goods_receipt_notes.csv') 
            invoice_df = pd.read_csv('data/vendor_invoices.csv')
            
            return po_df, grn_df, invoice_df
            
        except Exception as e:
            self.logger.error(f"Error loading matching data: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    def perform_three_way_match(self, invoice_id: str) -> Dict:
        """Perform comprehensive 3-way matching for a specific invoice"""
        
        po_df, grn_df, invoice_df = self.load_matching_data()
        
        if any(df.empty for df in [po_df, grn_df, invoice_df]):
            return {"error": "Unable to load matching data"}
        
        # Find the invoice
        invoice_row = invoice_df[invoice_df['invoice_id'] == invoice_id]
        if invoice_row.empty:
            return {"error": f"Invoice {invoice_id} not found"}
        
        invoice = invoice_row.iloc[0]
        
        # Find matching PO and GRN
        po_number = invoice.get('po_number', '')
        grn_number = invoice.get('grn_number', '')
        
        matching_po = po_df[po_df['po_number'] == po_number]
        matching_grn = grn_df[grn_df['grn_number'] == grn_number]
        
        if matching_po.empty or matching_grn.empty:
            return {
                "status": "incomplete_matching",
                "message": f"Missing matching documents - PO: {not matching_po.empty}, GRN: {not matching_grn.empty}",
                "action_required": "manual_review"
            }
        
        po = matching_po.iloc[0]
        grn = matching_grn.iloc[0]
        
        # Perform detailed matching
        matching_result = self._analyze_three_way_match(po, grn, invoice)
        
        # Generate AI insights
        ai_analysis = self._generate_ai_analysis(matching_result, po, grn, invoice)
        
        return {
            "status": matching_result["overall_status"],
            "invoice_id": invoice_id,
            "matching_details": matching_result,
            "ai_analysis": ai_analysis,
            "recommended_action": self._determine_action(matching_result),
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_three_way_match(self, po: pd.Series, grn: pd.Series, invoice: pd.Series) -> Dict:
        """Analyze matching between PO, GRN, and Invoice"""
        
        analysis = {
            "vendor_match": self._check_vendor_match(po, invoice),
            "quantity_match": self._check_quantity_match(po, grn, invoice),
            "price_match": self._check_price_match(po, invoice),
            "total_match": self._check_total_match(po, invoice),
            "date_validation": self._check_date_sequence(po, grn, invoice),
            "line_items_match": self._check_line_items(po, grn, invoice)
        }
        
        # Calculate overall score
        scores = [result.get("score", 0) for result in analysis.values()]
        overall_score = np.mean(scores) if scores else 0
        
        analysis["overall_score"] = overall_score
        analysis["overall_status"] = self._determine_status(overall_score)
        
        return analysis
    
    def _check_vendor_match(self, po: pd.Series, invoice: pd.Series) -> Dict:
        """Check if vendor information matches"""
        
        po_vendor = str(po.get('vendor_name', '')).strip().lower()
        invoice_vendor = str(invoice.get('vendor_name', '')).strip().lower()
        
        # Use fuzzy matching for vendor names
        similarity = difflib.SequenceMatcher(None, po_vendor, invoice_vendor).ratio()
        
        return {
            "match": similarity > 0.8,
            "score": similarity * 100,
            "po_vendor": po_vendor,
            "invoice_vendor": invoice_vendor,
            "similarity": similarity
        }
    
    def _check_quantity_match(self, po: pd.Series, grn: pd.Series, invoice: pd.Series) -> Dict:
        """Check quantity matching across all three documents"""
        
        po_qty = float(po.get('quantity', 0))
        grn_qty = float(grn.get('quantity_received', 0))  
        invoice_qty = float(invoice.get('quantity', 0))
        
        # Check if invoice quantity matches received quantity (GRN)
        qty_diff_percent = abs(grn_qty - invoice_qty) / grn_qty * 100 if grn_qty > 0 else 100
        
        within_tolerance = qty_diff_percent <= self.tolerance_config['quantity_tolerance_percent']
        
        return {
            "match": within_tolerance,
            "score": max(0, 100 - qty_diff_percent),
            "po_quantity": po_qty,
            "grn_quantity": grn_qty,
            "invoice_quantity": invoice_qty,
            "difference_percent": qty_diff_percent,
            "tolerance_used": self.tolerance_config['quantity_tolerance_percent']
        }
    
    def _check_price_match(self, po: pd.Series, invoice: pd.Series) -> Dict:
        """Check unit price matching between PO and Invoice"""
        
        po_price = float(po.get('unit_price', 0))
        invoice_price = float(invoice.get('unit_price', 0))
        
        price_diff_percent = abs(po_price - invoice_price) / po_price * 100 if po_price > 0 else 100
        within_tolerance = price_diff_percent <= self.tolerance_config['price_tolerance_percent']
        
        return {
            "match": within_tolerance,
            "score": max(0, 100 - price_diff_percent),
            "po_price": po_price,
            "invoice_price": invoice_price,
            "difference_percent": price_diff_percent,
            "tolerance_used": self.tolerance_config['price_tolerance_percent']
        }
    
    def _check_total_match(self, po: pd.Series, invoice: pd.Series) -> Dict:
        """Check total amount matching"""
        
        po_total = float(po.get('total_amount', 0))
        invoice_total = float(invoice.get('total_amount', 0))
        
        total_diff = abs(po_total - invoice_total)
        within_tolerance = total_diff <= self.tolerance_config['total_tolerance_amount']
        
        score = max(0, 100 - (total_diff / po_total * 100)) if po_total > 0 else 0
        
        return {
            "match": within_tolerance,
            "score": score,
            "po_total": po_total,
            "invoice_total": invoice_total,
            "difference_amount": total_diff,
            "tolerance_used": self.tolerance_config['total_tolerance_amount']
        }
    
    def _check_date_sequence(self, po: pd.Series, grn: pd.Series, invoice: pd.Series) -> Dict:
        """Check logical sequence of dates (PO -> GRN -> Invoice)"""
        
        try:
            po_date = pd.to_datetime(po.get('po_date'))
            grn_date = pd.to_datetime(grn.get('receipt_date'))
            invoice_date = pd.to_datetime(invoice.get('invoice_date'))
            
            logical_sequence = po_date <= grn_date <= invoice_date
            
            return {
                "match": logical_sequence,
                "score": 100 if logical_sequence else 0,
                "po_date": po_date.strftime('%Y-%m-%d'),
                "grn_date": grn_date.strftime('%Y-%m-%d'),
                "invoice_date": invoice_date.strftime('%Y-%m-%d'),
                "sequence_valid": logical_sequence
            }
            
        except Exception as e:
            return {
                "match": False,
                "score": 0,
                "error": f"Date parsing error: {e}"
            }
    
    def _check_line_items(self, po: pd.Series, grn: pd.Series, invoice: pd.Series) -> Dict:
        """Check line item details (simplified version)"""
        
        # In a real implementation, this would parse line item details
        # For demo, we'll do basic product/service matching
        
        po_description = str(po.get('description', '')).lower()
        invoice_description = str(invoice.get('description', '')).lower()
        
        similarity = difflib.SequenceMatcher(None, po_description, invoice_description).ratio()
        
        return {
            "match": similarity > 0.7,
            "score": similarity * 100,
            "po_description": po_description,
            "invoice_description": invoice_description,
            "similarity": similarity
        }
    
    def _determine_status(self, score: float) -> str:
        """Determine overall matching status based on score"""
        
        if score >= 95:
            return "perfect_match"
        elif score >= 85:
            return "acceptable_match"
        elif score >= 70:
            return "review_required"
        else:
            return "reject_match"
    
    def _determine_action(self, matching_result: Dict) -> str:
        """Determine recommended action based on matching results"""
        
        status = matching_result["overall_status"]
        
        if status == "perfect_match":
            return "auto_approve"
        elif status == "acceptable_match":
            return "approve_with_notification"
        elif status == "review_required":
            return "manual_review_required"
        else:
            return "reject_and_investigate"
    
    def _generate_ai_analysis(self, matching_result: Dict, po: pd.Series, grn: pd.Series, invoice: pd.Series) -> str:
        """Generate AI-powered analysis and recommendations"""
        
        context = f"""
        3-Way Matching Analysis:
        
        Overall Score: {matching_result['overall_score']:.1f}%
        Status: {matching_result['overall_status']}
        
        Detailed Results:
        - Vendor Match: {matching_result['vendor_match']['match']} (Score: {matching_result['vendor_match']['score']:.1f}%)
        - Quantity Match: {matching_result['quantity_match']['match']} (Score: {matching_result['quantity_match']['score']:.1f}%)
        - Price Match: {matching_result['price_match']['match']} (Score: {matching_result['price_match']['score']:.1f}%)
        - Total Match: {matching_result['total_match']['match']} (Score: {matching_result['total_match']['score']:.1f}%)
        - Date Sequence: {matching_result['date_validation']['match']} (Score: {matching_result['date_validation']['score']:.1f}%)
        
        Document Details:
        PO: {po['po_number']} - ${po['total_amount']} - {po['vendor_name']}
        GRN: {grn['grn_number']} - Qty: {grn['quantity_received']}
        Invoice: {invoice['invoice_id']} - ${invoice['total_amount']} - {invoice['vendor_name']}
        """
        
        prompt = f"""
        You are a Finance AI specialist analyzing a 3-way matching process for accounts payable.
        
        {context}
        
        Please provide:
        1. A clear summary of the matching results
        2. Identification of any red flags or concerns
        3. Specific recommendations for handling this invoice
        4. Risk assessment and potential financial impact
        5. Next steps for the finance team
        
        Keep your analysis concise but thorough (under 300 words).
        """
        
        try:
            response = genai.chat.completions.create(
                model=Config.GEMINI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert finance AI assistant specializing in accounts payable and fraud detection."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    def batch_process_matches(self, limit: int = 10) -> List[Dict]:
        """Process multiple invoices for 3-way matching"""
        
        _, _, invoice_df = self.load_matching_data()
        
        if invoice_df.empty:
            return []
        
        # Get pending invoices
        pending_invoices = invoice_df[invoice_df['status'] == 'pending'].head(limit)
        
        results = []
        for _, invoice in pending_invoices.iterrows():
            result = self.perform_three_way_match(invoice['invoice_id'])
            results.append(result)
        
        return results
    
    def get_matching_statistics(self) -> Dict:
        """Get statistics on matching performance"""
        
        try:
            _, _, invoice_df = self.load_matching_data()
            
            total_invoices = len(invoice_df)
            pending_invoices = len(invoice_df[invoice_df['status'] == 'pending'])
            
            # Simulate some matching history
            stats = {
                "total_invoices": total_invoices,
                "pending_matches": pending_invoices,
                "auto_approved_rate": 75.5,  # %
                "manual_review_rate": 20.2,  # %
                "rejected_rate": 4.3,        # %
                "avg_processing_time_hours": 2.1,
                "cost_savings_monthly": 15000,  # USD
                "accuracy_rate": 98.7         # %
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            return {}