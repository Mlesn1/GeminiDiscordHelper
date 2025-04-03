"""
AI service module for interacting with Google's Gemini 1.5 API.
"""
import logging
import asyncio
import google.generativeai as genai
from config import (
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
    GEMINI_TOP_K
)

logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service class for interacting with Gemini 1.5 AI."""
    
    def __init__(self):
        """Initialize the Gemini AI service with the API key and model configuration."""
        if not GEMINI_API_KEY:
            logger.critical("GEMINI_API_KEY not found in environment variables. AI service cannot initialize.")
            raise ValueError("GEMINI_API_KEY is required")
        
        # Configure the Gemini API client
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Store model configuration
        self.model_name = GEMINI_MODEL
        self.generation_config = {
            "max_output_tokens": GEMINI_MAX_TOKENS,
            "temperature": GEMINI_TEMPERATURE,
            "top_p": GEMINI_TOP_P,
            "top_k": GEMINI_TOP_K
        }
        
        logger.info(f"Initialized Gemini AI service with model: {self.model_name}")
    
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response from Gemini 1.5 based on the given prompt.
        
        Args:
            prompt: The text prompt to send to the AI.
            
        Returns:
            The generated text response.
            
        Raises:
            Exception: If there's an error in generating the response.
        """
        try:
            # Create a new model instance with the specified configuration
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
            
            # Use asyncio to run the model in a thread pool to avoid blocking
            response = await asyncio.to_thread(
                model.generate_content, 
                prompt
            )
            
            # Extract the text from the response
            if hasattr(response, 'text'):
                return response.text
            else:
                # Handle different response formats based on API version
                return str(response.candidates[0].content.parts[0].text)
                
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise Exception(f"Failed to generate AI response: {str(e)}")
