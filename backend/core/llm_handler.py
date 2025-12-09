# Groq or fallback LLM handler
"""
LLM Handler for generating answers using Groq API.

Key Features:
- Grounded generation (answers based ONLY on retrieved docs)
- Explainability (provides reasoning)
- Source citations (shows which laws used)
- Error handling and fallbacks

Model: llama-3.1-70b-versatile (Groq's best for reasoning)
"""
from groq import Groq
from typing import List, Dict, Optional
import json
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMHandler:
    """
    Handler for Groq LLM API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM handler.
        """
        self.api_key = api_key or settings.GROQ_API_KEY

        # 🔍 DEBUG: Confirm what type of key is loaded
        

        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY in .env")

        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)

        # Model configuration
        self.model = "llama-3.1-8b-instant" # Best for reasoning
        self.max_tokens = 1000  # Response length limit
        self.temperature = 0.3  # Low = more focused/consistent

        logger.info(f"✅ LLM Handler initialized")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   Temperature: {self.temperature}")

    # (rest of your file remains exactly the same)
    
    def create_prompt(self, query: str, retrieved_chunks: List[Dict], country: str) -> str:
        """
        Create a structured prompt for the LLM.
        
        This is the MOST IMPORTANT function - prompt quality = answer quality!
        
        Args:
            query: User's question
            retrieved_chunks: List of relevant document chunks from retriever
            country: Country context (india/canada/usa)
            
        Returns:
            Formatted prompt string
        """
        # Format retrieved documents
        context = self._format_context(retrieved_chunks)
        
        # Create the prompt with clear instructions
        prompt = f"""You are a legal information assistant specializing in {country.upper()} law. Your role is to provide accurate, helpful answers based ONLY on the provided legal documents.

LEGAL CONTEXT:
{context}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the LEGAL CONTEXT above
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question based on the provided documents"
3. Cite specific laws, sections, and acts when possible
4. Be concise but thorough
5. Use simple language that non-lawyers can understand

IMPORTANT: You must respond in the following JSON format:
{{
    "answer": "Your clear, direct answer to the question",
    "reasoning": "Explain which laws and sections support this answer",
    "sources": ["List of specific law titles or sections cited"],
    "confidence": "high/medium/low based on how well the context supports the answer"
}}

Respond ONLY with valid JSON, no additional text before or after."""

        return prompt
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into readable context.
        
        Args:
            chunks: List of document chunks with metadata
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant documents found."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"""
Document {i}:
Title: {chunk.get('title', 'Unknown')}
Section: {chunk.get('section', 'N/A')}
Category: {chunk.get('category', 'general')}
Content: {chunk.get('text', '')}
""")
        
        return "\n".join(context_parts)
    
    def generate_answer(
        self, 
        query: str, 
        retrieved_chunks: List[Dict], 
        country: str
    ) -> Dict:
        """
        Generate answer using Groq LLM.
        
        This is the main function that combines everything:
        1. Create prompt
        2. Call Groq API
        3. Parse response
        4. Return structured answer
        
        Args:
            query: User's question
            retrieved_chunks: Relevant documents from retriever
            country: Country context
            
        Returns:
            Dictionary with answer, reasoning, sources, confidence
        """
        try:
            # Step 1: Create prompt
            prompt = self.create_prompt(query, retrieved_chunks, country)
            
            logger.info(f"🤖 Generating answer for query: '{query}'")
            logger.info(f"   Country: {country}")
            logger.info(f"   Context chunks: {len(retrieved_chunks)}")
            
            # Step 2: Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal information assistant. Provide accurate, well-sourced answers based on legal documents. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                stream=False
            )
            
            # Step 3: Extract response
            raw_response = response.choices[0].message.content
            
            logger.info(f"✅ Received response from Groq")
            logger.info(f"   Tokens used: {response.usage.total_tokens}")
            
            # Step 4: Parse JSON response
            parsed_response = self._parse_response(raw_response)
            
            # Step 5: Add metadata
            parsed_response['raw_response'] = raw_response
            parsed_response['model'] = self.model
            parsed_response['tokens_used'] = response.usage.total_tokens
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return self._create_error_response(str(e))
    
    def _parse_response(self, raw_response: str) -> Dict:
        """
        Parse LLM response from JSON string.
        
        Args:
            raw_response: Raw JSON string from LLM
            
        Returns:
            Parsed dictionary
        """
        try:
            # Try to parse JSON
            parsed = json.loads(raw_response)
            
            # Validate required fields
            required_fields = ['answer', 'reasoning', 'sources']
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"⚠️ Missing field in response: {field}")
                    parsed[field] = "Not provided"
            
            # Ensure sources is a list
            if not isinstance(parsed.get('sources'), list):
                parsed['sources'] = [str(parsed.get('sources', 'Unknown'))]
            
            # Default confidence if not provided
            if 'confidence' not in parsed:
                parsed['confidence'] = 'medium'
            
            logger.info(f"✅ Successfully parsed JSON response")
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"   Raw response: {raw_response[:200]}...")
            
            # Fallback: try to extract answer from raw text
            return {
                'answer': raw_response[:500] if raw_response else "Error parsing response",
                'reasoning': "Could not parse structured response",
                'sources': [],
                'confidence': 'low',
                'parse_error': str(e)
            }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """
        Create error response when LLM call fails.
        
        Args:
            error_message: Error description
            
        Returns:
            Error response dictionary
        """
        return {
            'answer': "I'm sorry, I encountered an error generating a response.",
            'reasoning': f"Error: {error_message}",
            'sources': [],
            'confidence': 'low',
            'error': error_message
        }
    
    def validate_answer_quality(self, answer_dict: Dict, retrieved_chunks: List[Dict]) -> Dict:
        """
        Validate the quality of the generated answer.
        
        Checks:
        - Is answer substantive (not too short)?
        - Are sources cited?
        - Does reasoning reference the documents?
        
        Args:
            answer_dict: Generated answer dictionary
            retrieved_chunks: Original retrieved chunks
            
        Returns:
            Validation results with warnings
        """
        warnings = []
        
        # Check answer length
        answer = answer_dict.get('answer', '')
        if len(answer) < 20:
            warnings.append("Answer seems too short")
        
        # Check sources
        sources = answer_dict.get('sources', [])
        if not sources or len(sources) == 0:
            warnings.append("No sources cited")
        
        # Check reasoning
        reasoning = answer_dict.get('reasoning', '')
        if len(reasoning) < 30:
            warnings.append("Reasoning seems insufficient")
        
        # Check if sources match retrieved documents
        retrieved_titles = [chunk.get('title', '') for chunk in retrieved_chunks]
        cited_sources = answer_dict.get('sources', [])
        
        matches = sum(1 for source in cited_sources 
                     if any(title.lower() in source.lower() or source.lower() in title.lower() 
                            for title in retrieved_titles))
        
        if matches == 0 and len(retrieved_chunks) > 0:
            warnings.append("Sources don't match retrieved documents")
        
        return {
            'is_valid': len(warnings) == 0,
            'warnings': warnings,
            'quality_score': max(0, 1.0 - (len(warnings) * 0.2))
        }


# Global LLM handler instance
_llm_handler_instance = None


def get_llm_handler() -> LLMHandler:
    """
    Get or create global LLM handler instance.
    
    Returns:
        Singleton LLMHandler instance
    """
    global _llm_handler_instance
    
    if _llm_handler_instance is None:
        logger.info("🔄 Initializing global LLM handler...")
        _llm_handler_instance = LLMHandler()
    
    return _llm_handler_instance

