"""
Unit tests for InvoiceFollowupAgent
Tests core functionality to ensure reliability
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.invoice_followup_agent import InvoiceFollowupAgent
import pandas as pd

class TestInvoiceFollowupAgent(unittest.TestCase):
    """Test cases for Invoice Follow-up Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.agent = InvoiceFollowupAgent()
        
        # Create sample test data
        self.sample_invoice = {
            'invoice_id': 'INV001',
            'customer_id': 'CUST-101',
            'customer_name': 'Test Company',
            'customer_email': 'test@company.com',
            'invoice_amount': 5000.00,
            'issue_date': '2024-07-15',
            'due_date': '2024-08-15',
            'days_overdue': 50,
            'status': 'overdue',
            'payment_history_score': 7.5,
            'industry': 'Technology',
            'relationship_length_months': 24
        }
    
    def test_categorize_overdue_severity(self):
        """Test severity categorization logic"""
        
        # Test polite category
        self.assertEqual(
            self.agent.categorize_overdue_severity(15),
            "polite"
        )
        
        # Test firm category
        self.assertEqual(
            self.agent.categorize_overdue_severity(40),
            "firm"
        )
        
        # Test legal escalation
        self.assertEqual(
            self.agent.categorize_overdue_severity(70),
            "legal_escalation"
        )
    
    def test_get_customer_context(self):
        """Test customer context generation"""
        
        context = self.agent.get_customer_context(self.sample_invoice)
        
        # Check if key information is included
        self.assertIn('Test Company', context)
        self.assertIn('5000.00', context)
        self.assertIn('50', context)
        self.assertIn('Technology', context)
    
    def test_load_invoice_data(self):
        """Test invoice data loading"""
        
        df = self.agent.load_invoice_data()
        
        # Check if DataFrame is returned
        self.assertIsInstance(df, pd.DataFrame)
        
        # If data exists, check structure
        if not df.empty:
            required_columns = [
                'invoice_id', 'customer_name', 'invoice_amount', 
                'days_overdue', 'status'
            ]
            for col in required_columns:
                self.assertIn(col, df.columns)
    
    def test_prioritize_followups(self):
        """Test invoice prioritization logic"""
        
        # Create test DataFrame
        test_data = pd.DataFrame([
            {
                'invoice_id': 'INV001',
                'invoice_amount': 10000,
                'days_overdue': 60,
                'payment_history_score': 3,
                'status': 'overdue'
            },
            {
                'invoice_id': 'INV002',
                'invoice_amount': 5000,
                'days_overdue': 30,
                'payment_history_score': 8,
                'status': 'overdue'
            }
        ])
        
        prioritized = self.agent.prioritize_followups(test_data)
        
        # Check if priority_score column was added
        self.assertIn('priority_score', prioritized.columns)
        
        # Check if sorted correctly (highest first)
        scores = prioritized['priority_score'].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_email_generation_structure(self):
        """Test that email generation returns expected structure"""
        
        # This test requires API key - skip if not available
        if not self.agent.config.OPENAI_API_KEY:
            self.skipTest("OpenAI API key not configured")
        
        result = self.agent.generate_followup_email(self.sample_invoice)
        
        # Check result structure
        self.assertIsInstance(result, dict)
        self.assertIn('email_content', result)
        self.assertIn('ai_insights', result)
        self.assertIn('similar_cases', result)
        self.assertIn('recommended_follow_up_hours', result)
    
    def tearDown(self):
        """Clean up after tests"""
        pass

# Run tests
if __name__ == '__main__':
    unittest.main()