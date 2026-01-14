import redis
import json
import os
import hashlib
from typing import Optional, Any


class RedisCache:
    """
    Central Redis cache for Catalyst AI
    Used by:
    - Invoice Follow-up Agent
    - Vendor Query Agent
    - RAG responses
    - Analytics caching
    """

    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )

    # -------------------------
    # Generic helpers
    # -------------------------
    def _hash_key(self, raw_key: str) -> str:
        """Ensure cache key length safety"""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.client.get(self._hash_key(key))
            if value:
                return json.loads(value)
        except Exception:
            return None
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            self.client.setex(
                self._hash_key(key),
                ttl,
                json.dumps(value, default=str)
            )
        except Exception:
            pass

    def delete(self, key: str):
        try:
            self.client.delete(self._hash_key(key))
        except Exception:
            pass

    # -------------------------
    # Agent-specific helpers
    # -------------------------

    # 🔹 Invoice Follow-up caching
    def get_invoice_followup(self, invoice_id: str):
        return self.get(f"invoice_followup:{invoice_id}")

    def set_invoice_followup(self, invoice_id: str, email_text: str):
        self.set(
            key=f"invoice_followup:{invoice_id}",
            value={"email": email_text},
            ttl=24 * 3600  # 24 hours
        )

    # 🔹 Vendor query caching
    def get_vendor_query(self, vendor_id: str, query: str):
        return self.get(f"vendor_query:{vendor_id}:{query}")

    def set_vendor_query(self, vendor_id: str, query: str, response: dict):
        self.set(
            key=f"vendor_query:{vendor_id}:{query}",
            value=response,
            ttl=6 * 3600  # 6 hours
        )

    # 🔹 RAG response caching
    def get_rag_response(self, context_id: str, query: str):
        return self.get(f"rag:{context_id}:{query}")

    def set_rag_response(self, context_id: str, query: str, response: str):
        self.set(
            key=f"rag:{context_id}:{query}",
            value={"response": response},
            ttl=12 * 3600
        )

    # 🔹 Analytics caching
    def get_dashboard_metrics(self):
        return self.get("dashboard:metrics")

    def set_dashboard_metrics(self, metrics: dict):
        self.set(
            key="dashboard:metrics",
            value=metrics,
            ttl=900  # 15 min
        )
