"""Gemini API client with grounding support."""

import os
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types

# Response schema for structured output
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "Conversational response to the user"
        },
        "game_file": {
            "type": "string",
            "description": "Complete game file content in .nfg or .efg format. Only provide this when creating or updating a game file. Must start with 'NFG' or 'EFG'.",
            "nullable": True
        }
    },
    "required": ["message"]
}


class GeminiClient:
    """Client for interacting with Gemini API with Google Search grounding."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Set environment variable for genai client
        os.environ["GEMINI_API_KEY"] = self.api_key
        self.client = genai.Client()
        
        # Configure grounding tool
        self.grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        use_grounding: bool = True,
        use_structured_output: bool = False
    ) -> Dict[str, Any]:
        """Generate response from Gemini with optional grounding or structured output.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt to prepend.
            use_grounding: Whether to enable Google Search grounding (incompatible with structured output).
            use_structured_output: Whether to use structured output for game file generation.
            
        Returns:
            Dict with 'text', 'game_file', 'grounding_metadata', and 'sources' keys.
        """
        # Build contents for Gemini
        contents = []
        
        # Add system prompt as first user message if provided
        if system_prompt:
            contents.append(types.Content(
                role="user",
                parts=[types.Part(text=system_prompt)]
            ))
            contents.append(types.Content(
                role="model",
                parts=[types.Part(text="Understood. I'm ready to assist with game theory construction.")]
            ))
        
        # Add conversation history
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))
        
        # Configure generation based on mode
        # Note: Grounding cannot be used with structured output (controlled generation)
        if use_structured_output:
            # Structured output mode for game file generation
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA
            )
        else:
            # Normal mode with optional grounding
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
            if use_grounding:
                config.tools = [self.grounding_tool]
        
        # Generate response
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=contents,
                config=config
            )
            
            # Check if response has text
            if not hasattr(response, 'text') or response.text is None:
                raise RuntimeError("No text in response from Gemini API")
            
            # Parse response based on mode
            import json
            game_file = None
            
            if use_structured_output:
                # Parse structured JSON response
                try:
                    structured_response = json.loads(response.text)
                    message_text = structured_response.get("message", response.text)
                    game_file = structured_response.get("game_file")
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    message_text = response.text
            else:
                # Normal text response
                message_text = response.text
            
            result = {
                "text": message_text,
                "game_file": game_file,
                "grounding_metadata": None,
                "sources": []
            }
            
            # Extract grounding metadata if available
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    result["grounding_metadata"] = metadata
                    
                    # Extract sources
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        sources = []
                        try:
                            # grounding_chunks might be None even if hasattr returns True
                            chunks = metadata.grounding_chunks
                            if chunks is not None:
                                for chunk in chunks:
                                    if hasattr(chunk, 'web') and chunk.web:
                                        sources.append({
                                            "title": getattr(chunk.web, 'title', 'Unknown'),
                                            "uri": getattr(chunk.web, 'uri', '')
                                        })
                            result["sources"] = sources
                        except (TypeError, AttributeError):
                            # If grounding_chunks isn't iterable or has issues, skip it
                            pass
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    def generate_simple(self, prompt: str, use_grounding: bool = True) -> str:
        """Generate a simple response for a single prompt.
        
        Args:
            prompt: The prompt text.
            use_grounding: Whether to enable grounding.
            
        Returns:
            Response text.
        """
        messages = [{"role": "user", "content": prompt}]
        result = self.generate_response(messages, use_grounding=use_grounding)
        return result["text"]
