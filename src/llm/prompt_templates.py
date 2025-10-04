"""
Centralized prompt templates for consistency
All AI prompts are defined here for easy management
"""

class PromptTemplates:
    """Collection of prompt templates for various tasks"""
    
    # Email Generation Templates
    EMAIL_GENERATION_TEMPLATE = """
You are a Finance AI Assistant with access to customer intelligence data.

Customer Context:
{customer_context}

{rag_context}

Task: Write a {tone} email using a {approach} strategy about the overdue invoice.

IMPORTANT GUIDELINES:
1. Use the customer intelligence to personalize the message
2. Reference successful past interaction patterns if available
3. Adapt tone based on payment history and risk assessment
4. Include specific next steps based on customer's preferred communication style
5. Keep it concise (under 250 words)
6. Use proper business email format

Email Subject: Payment Reminder - Invoice {invoice_id}

Generate the email body:
"""
    
    # Intent Classification Template
    INTENT_CLASSIFICATION_TEMPLATE = """
Classify the following query into one of these categories:

Categories:
{categories}

Query: "{query}"

Respond with only the category name.
"""
    
    # Vendor Query Template
    VENDOR_QUERY_TEMPLATE = """
You are a helpful finance assistant for accounts payable.

Context: {context}
Question: "{query}"

Provide a brief, professional response. If you cannot answer specifically, 
direct them to contact accounts payable.

Keep response under 150 words.
"""
    
    # Fraud Analysis Template
    FRAUD_ANALYSIS_TEMPLATE = """
You are a Finance AI specialist analyzing potential fraud.

Invoice Details:
{invoice_context}

Risk Factors Detected:
{risk_factors}

Please provide:
1. Risk assessment summary (high/medium/low)
2. Specific concerns and red flags
3. Recommended next steps
4. Whether to approve, review, or reject

Keep analysis concise but thorough (under 300 words).
"""
    
    # 3-Way Matching Analysis Template
    THREE_WAY_MATCHING_TEMPLATE = """
You are a Finance AI specialist analyzing a 3-way matching process.

Matching Results:
{matching_context}

Document Details:
PO: {po_details}
GRN: {grn_details}
Invoice: {invoice_details}

Provide:
1. Clear summary of matching results
2. Any red flags or concerns
3. Specific recommendations
4. Risk assessment
5. Next steps for finance team

Keep analysis under 300 words.
"""
    
    @staticmethod
    def format_email_prompt(
        customer_context: str,
        rag_context: str,
        tone: str,
        approach: str,
        invoice_id: str
    ) -> str:
        """Format email generation prompt with variables"""
        
        return PromptTemplates.EMAIL_GENERATION_TEMPLATE.format(
            customer_context=customer_context,
            rag_context=rag_context,
            tone=tone,
            approach=approach,
            invoice_id=invoice_id
        )
    
    @staticmethod
    def format_intent_classification(query: str, categories: List[str]) -> str:
        """Format intent classification prompt"""
        
        categories_str = "\n".join([f"- {cat}" for cat in categories])
        
        return PromptTemplates.INTENT_CLASSIFICATION_TEMPLATE.format(
            categories=categories_str,
            query=query
        )