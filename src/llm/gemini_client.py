"""
Google Gemini API client wrapper
Handles API calls with error handling and retry logic
Alternative to OpenAI for cost-effective AI operations
"""

import google.generativeai as genai
import time
from typing import Dict, List, Optional
import logging
from config import Config

class GeminiClient:
    """Wrapper for Google Gemini API with best practices"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (defaults to Config.GEMINI_API_KEY)
        """
        self.api_key = api_key or Config.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.default_model = "gemini-1.5-flash"  # Fast and cost-effective
        # Available models: "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"
        
        self.default_temperature = 0.7
        self.max_retries = 3
        
        # Initialize model
        self.model = genai.GenerativeModel(self.default_model)
        
        # Safety settings (optional - adjust based on your needs)
        self.safety_settings = {
            "HARASSMENT": "BLOCK_NONE",
            "HATE_SPEECH": "BLOCK_NONE", 
            "SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "DANGEROUS_CONTENT": "BLOCK_NONE"
        }
    
    def generate_completion(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 500
    ) -> str:
        """
        Generate text completion with retry logic
        
        Args:
            prompt: The user's prompt/question
            system_instruction: System-level instructions for the model (like system message in OpenAI)
            model_name: Specific Gemini model to use
            temperature: Creativity level (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Why this structure:
        - Retry logic handles temporary API failures
        - System instruction sets AI's role/behavior
        - Temperature controls creativity vs consistency
        """
        
        model_name = model_name or self.default_model
        temperature = temperature or self.default_temperature
        
        # If system instruction provided, create new model with it
        if system_instruction:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        # Configure generation parameters
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        # Retry loop for handling API errors
        for attempt in range(self.max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
                
                # Extract text from response
                result = response.text.strip()
                
                # Log token usage if available
                if hasattr(response, 'usage_metadata'):
                    total_tokens = (
                        response.usage_metadata.prompt_token_count + 
                        response.usage_metadata.candidates_token_count
                    )
                    self.logger.info(f"Gemini API call successful. Tokens used: {total_tokens}")
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Handle rate limiting
                if "429" in error_msg or "quota" in error_msg.lower():
                    self.logger.warning(f"Rate limit hit. Attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    
                # Handle other API errors
                elif "API" in error_msg:
                    self.logger.error(f"Gemini API error: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(1)
                    
                # Handle unexpected errors
                else:
                    self.logger.error(f"Unexpected error: {e}")
                    raise
        
        raise Exception("Failed to generate completion after retries")
    
    def generate_email(
        self,
        customer_context: str,
        tone: str,
        approach: str,
        invoice_id: str
    ) -> str:
        """
        Specialized method for email generation
        
        Why separate method:
        - Encapsulates email-specific logic
        - Consistent prompt structure
        - Easy to modify email generation behavior
        
        Args:
            customer_context: Information about the customer
            tone: Email tone (friendly, firm, legal)
            approach: Communication approach
            invoice_id: Invoice identifier
            
        Returns:
            Generated email text
        """
        
        system_instruction = """You are an expert finance communication specialist with 10+ years 
        of experience in accounts receivable. You write professional, effective collection emails 
        that maintain good customer relationships while ensuring payment."""
        
        prompt = f"""
Write a {tone} email using a {approach} strategy for invoice collection.

Customer Context:
{customer_context}

Email Subject: Payment Reminder - Invoice {invoice_id}

Requirements:
1. Professional business format
2. Clear call-to-action
3. Empathetic yet firm tone
4. Under 250 words
5. Include payment details
6. Offer support if needed

Generate the email body now:
"""
        
        return self.generate_completion(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.7,
            max_tokens=400
        )
    
    def classify_text(
        self,
        text: str,
        categories: List[str]
    ) -> str:
        """
        Classify text into one of the given categories
        
        Why this method:
        - Intent classification for queries
        - Categorizing vendor requests
        - Routing user inputs
        
        Args:
            text: Text to classify
            categories: List of possible categories
            
        Returns:
            Category name as string
        """
        
        categories_str = "\n".join([f"- {cat}" for cat in categories])
        
        prompt = f"""
Classify the following text into EXACTLY ONE of these categories:

Categories:
{categories_str}

Text to classify: "{text}"

Rules:
- Respond with ONLY the category name
- No explanation or additional text
- Must be one of the categories listed above

Category:"""
        
        return self.generate_completion(
            prompt=prompt,
            temperature=0,  # Low temperature for consistent classification
            max_tokens=20
        )
    
    def extract_entities(
        self,
        text: str,
        entity_types: List[str]
    ) -> Dict:
        """
        Extract named entities from text
        
        Use cases:
        - Extract invoice numbers from vendor emails
        - Parse payment amounts from messages
        - Identify customer names in queries
        
        Args:
            text: Text to analyze
            entity_types: Types of entities to extract (e.g., ["invoice_number", "amount"])
            
        Returns:
            Dictionary with extracted entities
        """
        
        entities_str = ", ".join(entity_types)
        
        prompt = f"""
Extract the following entities from the text: {entities_str}

Text: "{text}"

Return ONLY a valid JSON object with extracted values. If an entity is not found, use null.

Example format:
{{
    "invoice_number": "INV001",
    "amount": 5000.00,
    "customer_name": "Tech Corp"
}}

JSON:"""
        
        result = self.generate_completion(
            prompt=prompt,
            temperature=0,
            max_tokens=200
        )
        
        # Parse JSON response safely
        try:
            import json
            # Remove markdown code blocks if present
            result = result.replace("```json", "").replace("```", "").strip()
            return json.loads(result)
        except Exception as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return {}
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of customer communication
        
        Why useful:
        - Gauge customer mood before sending collection email
        - Adjust tone based on customer sentiment
        - Flag angry customers for special handling
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment: "positive", "neutral", or "negative"
        """
        
        prompt = f"""
Analyze the sentiment of this customer communication:

"{text}"

Respond with ONLY ONE WORD: positive, neutral, or negative

Sentiment:"""
        
        return self.generate_completion(
            prompt=prompt,
            temperature=0,
            max_tokens=10
        ).lower()
    
    def summarize_text(self, text: str, max_length: int = 100) -> str:
        """
        Summarize long text into concise version
        
        Use cases:
        - Summarize long customer emails
        - Create brief notes from call transcripts
        - Dashboard summaries
        
        Args:
            text: Text to summarize
            max_length: Maximum words in summary
            
        Returns:
            Summarized text
        """
        
        prompt = f"""
Summarize the following text in {max_length} words or less:

{text}

Summary:"""
        
        return self.generate_completion(
            prompt=prompt,
            temperature=0.5,
            max_tokens=max_length * 2  # Roughly 2 tokens per word
        )
    
    def generate_with_context(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Generate response with conversation history (multi-turn chat)
        
        Why needed:
        - Follow-up questions in vendor chat
        - Context-aware responses
        - Conversation memory
        
        Args:
            messages: List of {"role": "user"/"model", "content": "text"} dicts
            system_instruction: Optional system instruction
            
        Returns:
            AI response text
        """
        
        # Build conversation history
        conversation_text = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {msg['content']}\n\n"
        
        # Add current query indicator
        conversation_text += "Assistant:"
        
        return self.generate_completion(
            prompt=conversation_text,
            system_instruction=system_instruction,
            temperature=0.7
        )
    
    def get_model_info(self) -> Dict:
        """
        Get information about available Gemini models
        
        Returns:
            Dictionary with model information
        """
        
        models_info = {
            "current_model": self.default_model,
            "available_models": {
                "gemini-1.5-flash": {
                    "description": "Fast and cost-effective, good for most tasks",
                    "context_window": "1M tokens",
                    "best_for": "High-volume operations, real-time responses"
                },
                "gemini-1.5-pro": {
                    "description": "Most capable, best performance",
                    "context_window": "2M tokens", 
                    "best_for": "Complex reasoning, long documents"
                },
                "gemini-pro": {
                    "description": "Balanced performance and cost",
                    "context_window": "32K tokens",
                    "best_for": "General purpose tasks"
                }
            }
        }
        
        return models_info
    
    def switch_model(self, model_name: str):
        """
        Switch to a different Gemini model
        
        Args:
            model_name: Name of model to switch to
        """
        
        try:
            self.model = genai.GenerativeModel(model_name)
            self.default_model = model_name
            self.logger.info(f"Switched to model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to switch model: {e}")
            raise
