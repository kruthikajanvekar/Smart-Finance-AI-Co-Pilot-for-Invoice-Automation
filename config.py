import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Gemini Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # Use a lighter default model to reduce token usage on free tier; override via GEMINI_MODEL env var
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.1")
    
    # Application Settings
    APP_NAME = "Finance AI Co-Pilot"
    VERSION = "0.1.0"
    
    # Data paths
    DATA_DIR = "data"
    SAMPLE_INVOICES_PATH = os.path.join(DATA_DIR, "sample_invoices.csv")
    CUSTOMER_HISTORY_PATH = os.path.join(DATA_DIR, "customer_history.csv")
    TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
    
    # RAG Configuration
    VECTOR_DB_PATH = "vector_db"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Email templates
    REMINDER_TYPES = ["polite", "firm", "legal_escalation"]
    
    # Business rules
    OVERDUE_THRESHOLD_DAYS = 30
    FIRM_REMINDER_DAYS = 45
    LEGAL_ESCALATION_DAYS = 60
    
    # Free tier settings (set FREE_TIER_MODE=false in .env to disable)
    FREE_TIER_MODE = os.getenv("FREE_TIER_MODE", "true").lower() == "true"
    FREE_TIER_CAP = int(os.getenv("FREE_TIER_CAP", "1"))
