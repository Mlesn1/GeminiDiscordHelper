"""
AI service module for interacting with Google's Gemini 1.5 API.
"""
import logging
import asyncio
import random
from typing import List, Dict, Optional, Tuple, Union

import google.generativeai as genai
from config import (
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    GEMINI_MAX_TOKENS,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
    GEMINI_TOP_K,
    GEMINI_SYSTEM_INSTRUCTIONS,
    ENABLE_CONVERSATION_MEMORY,
    ENABLE_MOOD_INDICATOR
)
from utils.conversation_memory import conversation_manager, Message

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
        
        # System instructions for the AI
        self.system_instructions = GEMINI_SYSTEM_INSTRUCTIONS
        
        logger.info(f"Initialized Gemini AI service with model: {self.model_name}")
    
    async def generate_response(self, prompt: str, user_id: Optional[int] = None, 
                               channel_id: Optional[int] = None, author_name: str = "") -> Tuple[str, Optional[str]]:
        """
        Generate a response from Gemini 1.5 based on the given prompt.
        
        Args:
            prompt: The text prompt to send to the AI.
            user_id: Optional Discord user ID for conversation memory.
            channel_id: Optional Discord channel ID for conversation memory.
            author_name: Name of the user sending the prompt.
            
        Returns:
            A tuple containing (response_text, conversation_preview).
            
        Raises:
            Exception: If there's an error in generating the response.
        """
        try:
            conversation_preview = None
            conversation_history = None
            mood_prefix = ""
            mood_suffix = ""
            mood_emoji = ""
            
            # Handle conversation memory if enabled
            if ENABLE_CONVERSATION_MEMORY:
                if user_id:
                    # User-specific conversation
                    conversation = conversation_manager.get_user_conversation(user_id)
                    conversation_manager.add_user_message(user_id, prompt, author_name)
                    conversation_history = conversation.get_formatted_history()
                    conversation_preview = conversation_manager.get_user_conversation_preview(user_id)
                    
                    # Get mood information if enabled
                    if ENABLE_MOOD_INDICATOR:
                        conversation.maybe_change_mood()
                        mood_prefix, mood_suffix = conversation.get_mood_decorator()
                        mood_emoji = conversation.get_mood_emoji()
                        
                elif channel_id:
                    # Channel-specific conversation
                    conversation = conversation_manager.get_channel_conversation(channel_id)
                    conversation_manager.add_channel_user_message(channel_id, user_id or 0, prompt, author_name)
                    conversation_history = conversation.get_formatted_history()
                    conversation_preview = conversation_manager.get_channel_conversation_preview(channel_id)
                    
                    # Get mood information if enabled
                    if ENABLE_MOOD_INDICATOR:
                        conversation.maybe_change_mood()
                        mood_prefix, mood_suffix = conversation.get_mood_decorator()
                        mood_emoji = conversation.get_mood_emoji()
            
            # Create a new model instance with the specified configuration
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
            
            # Prepare the content for the model based on whether we have conversation history
            if conversation_history:
                # Add system instructions as the first message if we have conversation history
                conversation_with_instructions = [
                    {"role": "system", "parts": [{"text": self.system_instructions}]}
                ] + conversation_history
                
                # Use conversation history to generate a contextual response
                response = await asyncio.to_thread(
                    model.generate_content,
                    conversation_with_instructions
                )
            else:
                # No conversation history, just use the prompt
                full_prompt = f"{self.system_instructions}\n\nUser: {prompt}\n\nAssistant:"
                response = await asyncio.to_thread(
                    model.generate_content,
                    full_prompt
                )
            
            # Extract the text from the response
            if hasattr(response, 'text'):
                response_text = response.text
            else:
                # Handle different response formats based on API version
                response_text = str(response.candidates[0].content.parts[0].text)
            
            # Apply mood styling if enabled
            if ENABLE_MOOD_INDICATOR and (mood_prefix or mood_suffix or mood_emoji):
                if mood_emoji:
                    styled_response = f"{mood_emoji} {mood_prefix}{response_text}{mood_suffix}"
                else:
                    styled_response = f"{mood_prefix}{response_text}{mood_suffix}"
            else:
                styled_response = response_text
            
            # Store the assistant's response in conversation memory if enabled
            if ENABLE_CONVERSATION_MEMORY:
                if user_id:
                    conversation_manager.add_assistant_message(user_id, response_text)
                elif channel_id:
                    conversation_manager.add_channel_assistant_message(channel_id, response_text)
            
            # Format the conversation preview for display
            formatted_preview = None
            if conversation_preview:
                formatted_preview = conversation_manager.format_preview_for_discord(conversation_preview)
            
            return styled_response, formatted_preview
                
        except Exception as e:
            logger.error(f"Error generating response from Gemini: {e}")
            raise Exception(f"Failed to generate AI response: {str(e)}")
    
    async def clear_conversation(self, user_id: Optional[int] = None, channel_id: Optional[int] = None) -> bool:
        """
        Clear conversation history for a user or channel.
        
        Args:
            user_id: Optional Discord user ID.
            channel_id: Optional Discord channel ID.
        
        Returns:
            True if the conversation was cleared, False otherwise.
        """
        if user_id:
            return conversation_manager.clear_user_conversation(user_id)
        elif channel_id:
            return conversation_manager.clear_channel_conversation(channel_id)
        return False
    
    async def get_conversation_preview(self, user_id: Optional[int] = None, channel_id: Optional[int] = None) -> Optional[str]:
        """
        Get the conversation preview for a user or channel.
        
        Args:
            user_id: Optional Discord user ID.
            channel_id: Optional Discord channel ID.
        
        Returns:
            Formatted conversation preview string or None if no conversation exists.
        """
        preview = None
        
        if user_id:
            preview = conversation_manager.get_user_conversation_preview(user_id)
        elif channel_id:
            preview = conversation_manager.get_channel_conversation_preview(channel_id)
        
        if preview:
            return conversation_manager.format_preview_for_discord(preview)
        
        return None
