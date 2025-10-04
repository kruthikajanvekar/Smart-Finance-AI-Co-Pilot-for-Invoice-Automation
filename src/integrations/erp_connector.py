
import requests
import pandas as pd
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta
from config import Config
import base64
import logging

class ERPConnector:
    """Base class for ERP integrations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_invoices(self) -> pd.DataFrame:
        raise NotImplementedError
    
    def get_customers(self) -> pd.DataFrame:
        raise NotImplementedError
    
    def get_payments(self) -> pd.DataFrame:
        raise NotImplementedError

class QuickBooksConnector(ERPConnector):
    """QuickBooks Online API integration"""
    
    def __init__(self, client_id: str, client_secret: str, access_token: str, company_id: str):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.company_id = company_id
        self.base_url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{company_id}"
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to QuickBooks API"""
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"QuickBooks API error: {e}")
            return {}
    
    def get_invoices(self) -> pd.DataFrame:
        """Fetch invoices from QuickBooks"""
        
        # Get invoices from last 90 days
        ninety_days_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        query = f"SELECT * FROM Invoice WHERE TxnDate >= '{ninety_days_ago}'"
        
        data = self._make_request('query', {'query': query})
        
        if not data or 'QueryResponse' not in data:
            return pd.DataFrame()
        
        invoices = data['QueryResponse'].get('Invoice', [])
        
        # Transform to our standard format
        invoice_data = []
        for invoice in invoices:
            
            # Calculate days overdue
            due_date = datetime.strptime(invoice.get('DueDate', ''), '%Y-%m-%d')
            days_overdue = max(0, (datetime.now() - due_date).days)
            
            # Determine status
            balance = float(invoice.get('Balance', 0))
            status = 'overdue' if balance > 0 and days_overdue > 0 else 'paid'
            
            invoice_data.append({
                'invoice_id': invoice.get('DocNumber', ''),
                'customer_id': invoice.get('CustomerRef', {}).get('value', ''),
                'customer_name': invoice.get('CustomerRef', {}).get('name', ''),
                'invoice_amount': float(invoice.get('TotalAmt', 0)),
                'issue_date': invoice.get('TxnDate', ''),
                'due_date': invoice.get('DueDate', ''),
                'days_overdue': days_overdue,
                'status': status,
                'balance': balance
            })
        
        return pd.DataFrame(invoice_data)
    
    def get_customers(self) -> pd.DataFrame:
        """Fetch customer data from QuickBooks"""
        
        data = self._make_request('query', {'query': "SELECT * FROM Customer"})
        
        if not data or 'QueryResponse' not in data:
            return pd.DataFrame()
        
        customers = data['QueryResponse'].get('Customer', [])
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'customer_id': customer.get('Id', ''),
                'customer_name': customer.get('Name', ''),
                'customer_email': customer.get('PrimaryEmailAddr', {}).get('Address', ''),
                'phone': customer.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
                'balance': float(customer.get('Balance', 0)),
                'active': customer.get('Active', True)
            })
        
        return pd.DataFrame(customer_data)

class SAPConnector(ERPConnector):
    """SAP Business One API integration"""
    
    def __init__(self, server_url: str, database: str, username: str, password: str):
        super().__init__()
        self.server_url = server_url
        self.database = database
        self.username = username  
        self.password = password
        self.session_id = None
        self.login()
    
    def login(self):
        """Authenticate with SAP Business One"""
        
        login_data = {
            "DatabaseServer": self.server_url,
            "DatabaseName": self.database,
            "UserName": self.username,
            "Password": self.password
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/Login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.session_id = response.cookies.get('B1SESSION')
                self.logger.info("Successfully logged into SAP Business One")
            else:
                self.logger.error(f"SAP login failed: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SAP connection error: {e}")
    
    def _make_sap_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Make authenticated request to SAP Business One"""
        
        if not self.session_id:
            self.login()
        
        headers = {
            'Content-Type': 'application/json',
            'Cookie': f'B1SESSION={self.session_id}'
        }
        
        url = f"{self.server_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            else:
                response = requests.post(url, headers=headers, json=data)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"SAP API error: {e}")
            return {}
    
    def get_invoices(self) -> pd.DataFrame:
        """Fetch invoices from SAP Business One"""
        
        # Query invoices with outstanding balance
        filter_query = "$filter=DocumentStatus eq 'O'"  # Open invoices only
        
        data = self._make_sap_request(f"Invoices?{filter_query}")
        
        if not data or 'value' not in data:
            return pd.DataFrame()
        
        invoices = data['value']
        
        invoice_data = []
        for invoice in invoices:
            
            # Calculate days overdue
            due_date = datetime.strptime(invoice.get('DocDueDate', '')[:10], '%Y-%m-%d')
            days_overdue = max(0, (datetime.now() - due_date).days)
            
            invoice_data.append({
                'invoice_id': invoice.get('DocNum', ''),
                'customer_id': invoice.get('CardCode', ''),
                'customer_name': invoice.get('CardName', ''),
                'invoice_amount': float(invoice.get('DocTotal', 0)),
                'issue_date': invoice.get('DocDate', '')[:10],
                'due_date': invoice.get('DocDueDate', '')[:10],
                'days_overdue': days_overdue,
                'status': 'overdue' if days_overdue > 0 else 'current',
                'balance': float(invoice.get('DocTotalSys', 0))
            })
        
        return pd.DataFrame(invoice_data)

class ERPDataManager:
    """Manager class to handle multiple ERP connections and data synchronization"""
    
    def __init__(self):
        self.connectors = {}
        self.logger = logging.getLogger(__name__)
    
    def add_connector(self, name: str, connector: ERPConnector):
        """Add an ERP connector"""
        self.connectors[name] = connector
        self.logger.info(f"Added {name} connector")
    
    def sync_data(self) -> Dict[str, pd.DataFrame]:
        """Sync data from all connected ERPs"""
        
        combined_data = {
            'invoices': pd.DataFrame(),
            'customers': pd.DataFrame(),
            'payments': pd.DataFrame()
        }
        
        for name, connector in self.connectors.items():
            try:
                self.logger.info(f"Syncing data from {name}")
                
                # Get invoices
                invoices = connector.get_invoices()
                if not invoices.empty:
                    invoices['source_erp'] = name
                    combined_data['invoices'] = pd.concat([combined_data['invoices'], invoices], ignore_index=True)
                
                # Get customers  
                customers = connector.get_customers()
                if not customers.empty:
                    customers['source_erp'] = name
                    combined_data['customers'] = pd.concat([combined_data['customers'], customers], ignore_index=True)
                
                self.logger.info(f"Successfully synced {len(invoices)} invoices and {len(customers)} customers from {name}")
                
            except Exception as e:
                self.logger.error(f"Error syncing data from {name}: {e}")
        
        # Remove duplicates and save to CSV
        self._save_synced_data(combined_data)
        
        return combined_data
    
    def _save_synced_data(self, data: Dict[str, pd.DataFrame]):
        """Save synced data to CSV files"""
        
        try:
            if not data['invoices'].empty:
                # Remove duplicates based on invoice_id
                data['invoices'].drop_duplicates(subset=['invoice_id'], keep='last', inplace=True)
                data['invoices'].to_csv('data/synced_invoices.csv', index=False)
                
            if not data['customers'].empty:
                data['customers'].drop_duplicates(subset=['customer_id'], keep='last', inplace=True)
                data['customers'].to_csv('data/synced_customers.csv', index=False)
                
            self.logger.info("Synced data saved to CSV files")
            
        except Exception as e:
            self.logger.error(f"Error saving synced data: {e}")
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time business metrics"""
        
        try:
            invoices_df = pd.read_csv('data/synced_invoices.csv')
            
            metrics = {
                'total_outstanding': invoices_df[invoices_df['status'] == 'overdue']['invoice_amount'].sum(),
                'overdue_count': len(invoices_df[invoices_df['status'] == 'overdue']),
                'avg_days_overdue': invoices_df[invoices_df['status'] == 'overdue']['days_overdue'].mean(),
                'total_invoices': len(invoices_df),
                'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {}

# Example usage and configuration
def setup_erp_connections():
    """Setup ERP connections based on environment variables"""
    
    manager = ERPDataManager()
    
    # QuickBooks setup (if credentials available)
    qb_client_id = os.getenv('QUICKBOOKS_CLIENT_ID')
    qb_client_secret = os.getenv('QUICKBOOKS_CLIENT_SECRET') 
    qb_access_token = os.getenv('QUICKBOOKS_ACCESS_TOKEN')
    qb_company_id = os.getenv('QUICKBOOKS_COMPANY_ID')
    
    if all([qb_client_id, qb_client_secret, qb_access_token, qb_company_id]):
        qb_connector = QuickBooksConnector(qb_client_id, qb_client_secret, qb_access_token, qb_company_id)
        manager.add_connector('QuickBooks', qb_connector)
    
    # SAP setup (if credentials available)
    sap_server = os.getenv('SAP_SERVER_URL')
    sap_database = os.getenv('SAP_DATABASE')
    sap_username = os.getenv('SAP_USERNAME')
    sap_password = os.getenv('SAP_PASSWORD')
    
    if all([sap_server, sap_database, sap_username, sap_password]):
        sap_connector = SAPConnector(sap_server, sap_database, sap_username, sap_password)
        manager.add_connector('SAP', sap_connector)
    
    return manager