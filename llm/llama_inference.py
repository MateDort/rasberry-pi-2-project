"""
LLM inference module using llama.cpp Python bindings.
"""
import logging
import os
from typing import Optional, List

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")

logger = logging.getLogger(__name__)


class LlamaInference:
    """Handles LLM inference using llama.cpp."""
    
    def __init__(
        self,
        model_path: str,
        temperature: float = 0.7,
        max_tokens: int = 150,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
        context_window: int = 2048,
        n_threads: Optional[int] = None
    ):
        """
        Initialize LLM inference engine.
        
        Args:
            model_path: Path to GGUF model file
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            repeat_penalty: Penalty for repeating tokens
            context_window: Context window size
            n_threads: Number of threads (None = auto)
        """
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python is not installed. Install with: pip install llama-cpp-python")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at: {model_path}")
        
        try:
            # Determine thread count (use all available cores for Pi Zero 2 W)
            if n_threads is None:
                # Raspberry Pi Zero 2 W has 4 cores
                n_threads = 4
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=context_window,
                n_threads=n_threads,
                verbose=False
            )
            
            self.temperature = temperature
            self.max_tokens = max_tokens
            self.top_p = top_p
            self.repeat_penalty = repeat_penalty
            
            logger.info(f"LLM model loaded from: {model_path}")
            logger.info(f"Context window: {context_window}, Threads: {n_threads}")
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise
    
    def _format_prompt(self, question: str, system_prompt: Optional[str] = None) -> str:
        """
        Format prompt for the model.
        
        Args:
            question: User's question
            system_prompt: Optional system prompt
            
        Returns:
            Formatted prompt string
        """
        if system_prompt:
            return f"{system_prompt}\n\nUser: {question}\nAssistant:"
        else:
            # Default prompt for Q&A
            return f"Question: {question}\nAnswer:"
    
    def generate(
        self,
        question: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response to a question.
        
        Args:
            question: User's question
            system_prompt: Optional system prompt
            stream: Whether to stream the response (not implemented yet)
            max_tokens: Override default max_tokens for this call
            
        Returns:
            Generated response text
        """
        try:
            prompt = self._format_prompt(question, system_prompt)
            
            logger.debug(f"Generating response for: {question[:50]}...")
            
            # Use provided max_tokens or default
            tokens_to_generate = max_tokens if max_tokens is not None else self.max_tokens
            
            response = self.llm(
                prompt,
                max_tokens=tokens_to_generate,
                temperature=self.temperature,
                top_p=self.top_p,
                repeat_penalty=self.repeat_penalty,
                stop=["\n\n", "User:", "Question:"],
                echo=False
            )
            
            # Extract text from response
            if isinstance(response, dict):
                text = response.get('choices', [{}])[0].get('text', '')
            else:
                text = str(response)
            
            # Clean up the response
            text = text.strip()
            
            # Remove any remaining prompt artifacts
            if text.startswith("Answer:"):
                text = text[7:].strip()
            
            logger.info(f"Generated response: {text[:100]}...")
            return text
            
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            return "I'm sorry, I encountered an error processing your question."
    
    def cleanup(self):
        """Clean up resources."""
        # llama-cpp-python handles cleanup automatically
        logger.info("LLM inference handler cleaned up")

