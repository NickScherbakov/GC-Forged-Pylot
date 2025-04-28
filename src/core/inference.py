"""
Inference logic for llama.cpp integration.
"""
import logging
import time
from typing import Dict, Any, List, Optional, Iterator, Union

logger = logging.getLogger(__name__)

class LlamaInference:
    """
    Handler for LLM inference operations with performance optimizations
    for Windows Server and specific hardware configurations.
    """
    
    def __init__(self, llama_instance):
        """
        Initialize the inference handler with a llama instance.
        
        Args:
            llama_instance: Initialized llama.cpp model instance
        """
        self.llama = llama_instance
        self.history = []
        self.max_history_size = 10
        
    def completion(self, 
                   prompt: str, 
                   max_tokens: int = 256, 
                   temperature: float = 0.7, 
                   top_p: float = 0.95, 
                   stop_sequences: List[str] = None,
                   stream: bool = False) -> Union[str, Iterator[str]]:
        """
        Generate a completion from the LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (higher = more creative)
            top_p: Nucleus sampling parameter
            stop_sequences: Sequences that stop generation when encountered
            stream: Whether to stream the output
            
        Returns:
            Generated text or stream iterator
        """
        start_time = time.time()
        stop_sequences = stop_sequences or []
        
        logger.debug(f"Starting inference with {len(prompt)} chars, temp={temperature}")
        
        try:
            if stream:
                return self._streaming_inference(prompt, max_tokens, temperature, top_p, stop_sequences)
            else:
                result = self._synchronous_inference(prompt, max_tokens, temperature, top_p, stop_sequences)
                
                # Log performance metrics
                elapsed = time.time() - start_time
                tokens = len(result.split())
                logger.debug(f"Generated {tokens} tokens in {elapsed:.2f}s ({tokens/elapsed:.2f} tokens/s)")
                
                # Store in history
                self._add_to_history(prompt, result)
                
                return result
                
        except Exception as e:
            logger.error(f"Inference error: {str(e)}")
            return "" if not stream else iter([""])
    
    def _synchronous_inference(self, prompt, max_tokens, temperature, top_p, stop):
        """Generate text synchronously."""
        params = self._prepare_inference_params(prompt, max_tokens, temperature, top_p)
        
        # Add stop sequences if provided
        if stop:
            params["stop"] = stop
            
        result = self.llama.create_completion(**params)
        return result["choices"][0]["text"]
    
    def _streaming_inference(self, prompt, max_tokens, temperature, top_p, stop):
        """Generate text as a stream."""
        params = self._prepare_inference_params(prompt, max_tokens, temperature, top_p, stream=True)
        
        # Add stop sequences if provided
        if stop:
            params["stop"] = stop
        
        # Create accumulator for history
        complete_text = ""
        
        # Stream tokens
        for chunk in self.llama.create_completion(**params):
            token = chunk["choices"][0]["text"]
            complete_text += token
            yield token
            
        # Store in history after completion
        self._add_to_history(prompt, complete_text)
    
    def _prepare_inference_params(self, prompt, max_tokens, temperature, top_p, stream=False):
        """Prepare parameters for inference call."""
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "stream": stream
        }
        
    def _add_to_history(self, prompt, response):
        """Add interaction to history cache."""
        self.history.append({
            "prompt": prompt,
            "response": response,
            "timestamp": time.time()
        })
        
        # Maintain history size
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
            
    def clear_history(self):
        """Clear interaction history."""
        self.history = []
        logger.debug("Inference history cleared")