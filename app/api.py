from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.invoice_followup_agent import InvoiceFollowupAgent
from agents.vendor_query_agent import VendorQueryAgent

# Initialize FastAPI app
app = FastAPI(
    title="Finance AI Co-Pilot API",
    description="REST API for AI-powered finance automation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
invoice_agent = InvoiceFollowupAgent()
vendor_agent = VendorQueryAgent()

# Pydantic models for request/response
class InvoiceFollowupRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=20, description="Number of follow-ups to generate")
    min_amount: Optional[float] = Field(default=None, description="Minimum invoice amount filter")
    min_days_overdue: Optional[int] = Field(default=None, description="Minimum days overdue filter")

class InvoiceFollowupResponse(BaseModel):
    status: str
    count: int
    followups: List[Dict]

class VendorQueryRequest(BaseModel):
    query: str = Field(..., description="Vendor query text")
    vendor_email: Optional[str] = Field(default=None, description="Vendor email for identification")

class VendorQueryResponse(BaseModel):
    status: str
    response: str
    data: Optional[Dict] = None

# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "operational",
        "message": "Finance AI Co-Pilot API v1.0.0",
        "endpoints": [
            "/invoices/followups",
            "/vendor/query",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents": {
            "invoice_agent": "operational",
            "vendor_agent": "operational"
        },
        "timestamp": pd.Timestamp.now().isoformat()
    }

@app.post("/invoices/followups", response_model=InvoiceFollowupResponse)
async def generate_followups(request: InvoiceFollowupRequest):
    """
    Generate AI-powered invoice follow-up emails
    
    - **limit**: Number of follow-ups to generate (1-20)
    - **min_amount**: Optional filter by minimum amount
    - **min_days_overdue**: Optional filter by days overdue
    """
    
    try:
        # Generate follow-ups
        followups = invoice_agent.generate_batch_followups(request.limit)
        
        # Apply filters if provided
        if request.min_amount:
            followups = [f for f in followups if f['amount'] >= request.min_amount]
        
        if request.min_days_overdue:
            followups = [f for f in followups if f['days_overdue'] >= request.min_days_overdue]
        
        return InvoiceFollowupResponse(
            status="success",
            count=len(followups),
            followups=followups
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/vendor/query", response_model=VendorQueryResponse)
async def process_vendor_query(request: VendorQueryRequest):
    """
    Handle vendor queries with AI assistance
    
    - **query**: Vendor's question or request
    - **vendor_email**: Optional email for vendor identification
    """
    
    try:
        result = vendor_agent.process_vendor_query(
            query=request.query,
            vendor_email=request.vendor_email
        )
        
        return VendorQueryResponse(
            status=result['status'],
            response=result['response'],
            data=result.get('data')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/invoices/summary")
async def get_invoice_summary():
    """Get summary statistics of invoices"""
    
    try:
        df = invoice_agent.load_invoice_data()
        
        if df.empty:
            return {"message": "No invoice data available"}
        
        overdue_df = df[df['status'] == 'overdue']
        
        return {
            "total_invoices": len(df),
            "overdue_count": len(overdue_df),
            "total_overdue_amount": float(overdue_df['invoice_amount'].sum()),
            "avg_days_overdue": float(overdue_df['days_overdue'].mean()) if len(overdue_df) > 0 else 0,
            "top_overdue_customers": overdue_df.nlargest(5, 'invoice_amount')[
                ['customer_name', 'invoice_amount', 'days_overdue']
            ].to_dict('records')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run with: uvicorn api:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)