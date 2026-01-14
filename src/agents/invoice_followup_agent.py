import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import google.generativeai as genai
from config import Config
import time
from google.api_core.exceptions import ResourceExhausted
from src.logger.logger import get_logger
logger = get_logger(__name__)


genai.configure(api_key=Config.GOOGLE_API_KEY)

class InvoiceFollowupAgent:
    def __init__(self):
        # API key configured in config.py
        self.config = Config()
        
    def load_invoice_data(self) -> pd.DataFrame:
        """Load invoice data from CSV file"""
        try:
            return pd.read_csv(Config.SAMPLE_INVOICES_PATH)
        except Exception as e:
            print(f"Error loading invoice data: {e}")
            return pd.DataFrame()
    
    def categorize_overdue_severity(self, days_overdue: int) -> str:
        """Categorize invoice based on how overdue it is"""
        if days_overdue <= Config.OVERDUE_THRESHOLD_DAYS:
            return "polite"
        elif days_overdue <= Config.FIRM_REMINDER_DAYS:
            return "firm"
        else:
            return "legal_escalation"
    
    def get_customer_context(self, customer_data: Dict) -> str:
        """Generate customer context for personalized communication"""
        context = f"""
        Customer: {customer_data['customer_name']}
        Industry: {customer_data['industry']}
        Relationship Length: {customer_data['relationship_length_months']} months
        Payment History Score: {customer_data['payment_history_score']}/10
        Last Payment: {customer_data['last_payment_date']}
        Invoice Amount: ${customer_data['invoice_amount']:,.2f}
        Days Overdue: {customer_data['days_overdue']}
        """
        return context
    
    def generate_followup_email(self, invoice_data: Dict, max_retries: int = 3, use_template_only: bool = False) -> str:
        """Generate personalized follow-up email using LLM with retry logic"""
        
        severity = self.categorize_overdue_severity(invoice_data['days_overdue'])
        customer_context = self.get_customer_context(invoice_data)
        
        # Dynamic prompt based on severity and customer context
        if severity == "polite":
            tone = "friendly and professional"
            urgency = "gentle reminder"
        elif severity == "firm":
            tone = "professional but more direct"
            urgency = "firm but respectful follow-up"
        else:
            tone = "formal and serious"
            urgency = "final notice before escalation"
        
        # If caller requests template-only mode, skip LLM and return fallback immediately
        if use_template_only:
            return "(Template fallback forced)\n\n" + self._template_fallback(invoice_data, tone)

        # Very short prompt to minimize token usage (helps free tier)
        prompt = (
            f"Compose a short professional invoice follow-up email (<=100 words) for {invoice_data['customer_name']}. "
            f"Invoice {invoice_data['invoice_id']} of ${invoice_data['invoice_amount']:,.2f} is {invoice_data['days_overdue']} days overdue. "
            f"Tone: {tone}. Include a clear call-to-action and polite closing. Output only the email body."
        )
        
        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(Config.GEMINI_MODEL)
                response = model.generate_content(
                    [
                        "You are a professional finance communication specialist.",
                        prompt
                    ],
                    generation_config={
                        "temperature": 0.4,
                        "max_output_tokens": 120
                    }
                )

                # If response is streaming/wrapped, try to resolve/finish it so content is available
                try:
                    if hasattr(response, "resolve"):
                        response.resolve()
                except Exception:
                    pass

                # Robustly extract text from various Gemini response shapes
                def _extract_text(resp) -> str:
                    # 1) Quick text accessor
                    try:
                        if hasattr(resp, "text") and isinstance(resp.text, str) and resp.text.strip():
                            return resp.text.strip()
                    except Exception:
                        pass

                    # 2) Try resp.to_dict() which many SDK response wrappers provide
                    resp_dict = None
                    try:
                        if hasattr(resp, "to_dict"):
                            resp_dict = resp.to_dict()
                    except Exception:
                        resp_dict = None

                    # 3) If to_dict not present, try protobuf conversion
                    if resp_dict is None:
                        try:
                            from google.protobuf.json_format import MessageToDict
                            # check common protobuf holders on the response wrapper
                            pb = getattr(resp, "_pb", None) or getattr(resp, "_result", None) or getattr(resp, "result", None)
                            if pb is not None:
                                resp_dict = MessageToDict(pb)
                        except Exception:
                            resp_dict = None

                    # Helper: recursively search a dict/list for 'parts' or 'text' fields
                    def _search_for_text(obj):
                        if obj is None:
                            return None
                        if isinstance(obj, str):
                            return obj if obj.strip() else None
                        if isinstance(obj, dict):
                            # direct text
                            if "text" in obj and isinstance(obj["text"], str) and obj["text"].strip():
                                return obj["text"].strip()
                            # parts list
                            if "parts" in obj and isinstance(obj["parts"], list):
                                parts = obj["parts"]
                                out = []
                                for p in parts:
                                    if isinstance(p, str) and p.strip():
                                        out.append(p)
                                    elif isinstance(p, dict):
                                        t = p.get("text") or p.get("content")
                                        if isinstance(t, str) and t.strip():
                                            out.append(t)
                                if out:
                                    return "".join(out)
                            # candidates
                            if "candidates" in obj and isinstance(obj["candidates"], list):
                                for cand in obj["candidates"]:
                                    if isinstance(cand, dict):
                                        content = cand.get("content")
                                        found = _search_for_text(content)
                                        if found:
                                            return found
                            # deeper search
                            for v in obj.values():
                                found = _search_for_text(v)
                                if found:
                                    return found
                            return None
                        if isinstance(obj, list):
                            for item in obj:
                                found = _search_for_text(item)
                                if found:
                                    return found
                            return None
                        return None

                    # 4) If we have a dict representation, search it
                    if resp_dict is not None:
                        found = _search_for_text(resp_dict)
                        if found:
                            return found

                    # 5) Try some top-level attributes we saw in SDKs
                    try:
                        top_parts = getattr(resp, "parts", None)
                        if top_parts:
                            out = []
                            for p in top_parts:
                                if isinstance(p, str) and p.strip():
                                    out.append(p)
                                elif isinstance(p, dict):
                                    t = p.get("text") or p.get("content")
                                    if isinstance(t, str) and t.strip():
                                        out.append(t)
                            if out:
                                return "".join(out)
                    except Exception:
                        pass

                    # 6) Try top-level candidates attribute
                    try:
                        top_candidates = getattr(resp, "candidates", None)
                        if top_candidates and len(top_candidates) > 0:
                            first = top_candidates[0]
                            content = first.get("content") if isinstance(first, dict) else getattr(first, "content", None)
                            found = _search_for_text(content)
                            if found:
                                return found
                    except Exception:
                        pass

                    # 7) Fallback to string repr (last resort)
                    try:
                        s = str(resp)
                        return s
                    except Exception:
                        return ""

                # Try converting protobuf to dict if available to extract parts
                try:
                    from google.protobuf.json_format import MessageToDict
                    pb = getattr(response, "_pb", None) or getattr(response, "result", None)
                    if pb is not None:
                        d = MessageToDict(pb)
                        # look for candidates -> content -> parts
                        candidates = d.get("candidates") if isinstance(d, dict) else None
                        if candidates and len(candidates) > 0:
                            first = candidates[0]
                            content = first.get("content") if isinstance(first, dict) else None
                            if content:
                                parts = content.get("parts")
                                if parts:
                                    return "".join([p for p in parts])
                except Exception:
                    pass

                generated_text = _extract_text(response)

                # If extraction produced usable text, return it
                if generated_text and not str(generated_text).strip().startswith("response:") and len(str(generated_text).strip()) > 20:
                    return generated_text.strip()

                # Otherwise fall back to a deterministic template so app still produces an email
                print("⚠️ LLM returned no usable text; using template fallback.")
                fallback = self._template_fallback(invoice_data, tone)
                return "(Template fallback due to LLM response)\n\n" + fallback
                
            except Exception as e:
                error_str = str(e)
                
                # Check if it's a quota/rate limit error
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry-after time if available
                        retry_after = 45  # default wait time
                        if "retry" in error_str.lower():
                            try:
                                import re
                                match = re.search(r'(\d+)\s*s', error_str)
                                if match:
                                    retry_after = int(match.group(1)) + 2
                            except:
                                pass
                        
                        wait_time = min(retry_after * (2 ** attempt), 120)  # Exponential backoff, max 2 min
                        print(f"⏳ Quota exceeded. Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"⚠️ Error generating email: Quota exceeded. Please wait a few minutes and try again.\nDetails: {error_str}"
                else:
                    # For non-quota errors, return immediately
                    return f"❌ Error generating email: {error_str}"
        
        return "❌ Failed to generate email after multiple retries"
    
    def prioritize_followups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prioritize follow-ups based on amount, days overdue, and payment history"""
        
        # Calculate priority score
        df['priority_score'] = (
            df['invoice_amount'] * 0.4 +  # 40% weight on amount
            df['days_overdue'] * 100 * 0.4 +  # 40% weight on overdue days
            (10 - df['payment_history_score']) * 1000 * 0.2  # 20% weight on payment history (inverted)
        )
        
        return df.sort_values('priority_score', ascending=False)

    def _template_fallback(self, invoice_data: Dict, tone: str) -> str:
        """Generate a simple templated follow-up email when LLM is unavailable."""
        customer = invoice_data.get('customer_name', 'Customer')
        invoice_id = invoice_data.get('invoice_id', 'N/A')
        amount = invoice_data.get('invoice_amount', 0.0)
        days = invoice_data.get('days_overdue', 0)

        salutation = f"Dear {customer},"
        body = (
            f"This is a {tone} reminder that invoice {invoice_id} for ${amount:,.2f} "
            f"is {days} days overdue. Please let us know the payment status or arrange payment at your earliest convenience. "
            "If you've already paid, please disregard this notice."
        )
        closing = "\n\nBest regards,\nAccounts Receivable Team"

        return f"{salutation}\n\n{body}{closing}"
    
    def generate_batch_followups(self, limit: int = 1, delay_between_requests: int = 60, use_template_only: bool = False) -> List[Dict]:
        """Generate follow-up emails for top priority invoices
        
        Args:
            limit: Number of emails to generate
            delay_between_requests: Seconds to wait between API calls (default 60s for free tier)
        """
        
        # Enforce free-tier caps if enabled in config
        if getattr(Config, "FREE_TIER_MODE", False):
            cap = getattr(Config, "FREE_TIER_CAP", 1)
            if limit > cap:
                print(f"⚠️ Free-tier mode active: capping requests to {cap} (you requested {limit}).")
                print("To disable this behavior set FREE_TIER_MODE=false in your .env when you have billing enabled.")
                limit = cap

        df = self.load_invoice_data()
        if df.empty:
            return []
        
        # Filter only overdue invoices
        overdue_df = df[df['status'] == 'overdue']
        
        # Prioritize
        prioritized_df = self.prioritize_followups(overdue_df)
        
        # Take top N
        top_invoices = prioritized_df.head(limit)
        
        results = []
        for idx, (_, invoice) in enumerate(top_invoices.iterrows()):
            # Add delay between requests for free tier (except for first request)
            if idx > 0:
                print(f"⏳ Waiting {delay_between_requests}s before next request to respect free tier limits...")
                time.sleep(delay_between_requests)
            
            email_content = self.generate_followup_email(invoice.to_dict(), use_template_only=use_template_only)
            # Ensure generated_email is always a string for the UI and record source
            source = 'TEMPLATE'
            if isinstance(email_content, str) and not email_content.startswith('(Template'):
                source = 'LLM'

            if not isinstance(email_content, str):
                try:
                    email_content = str(email_content)
                except Exception:
                    email_content = repr(email_content)
            
            results.append({
                'invoice_id': invoice['invoice_id'],
                'customer_name': invoice['customer_name'],
                'customer_email': invoice['customer_email'],
                'amount': invoice['invoice_amount'],
                'days_overdue': invoice['days_overdue'],
                'severity': self.categorize_overdue_severity(invoice['days_overdue']),
                'priority_score': invoice['priority_score'],
                'generated_email': email_content
                , 'generated_by': source
            })
        
        return results