"""
Core server implementation that interfaces with llama.cpp.
"""
import os
import sys
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LlamaServer:
    """
    A wrapper around llama.cpp that provides enhanced functionality
    for IDE integration and continuous operation.
    """
    
    def __init__(self, model_path=None, config=None):
        """
        Initialize the LlamaServer with model path and configuration.
        
        Args:
            model_path: Path to the GGUF model file
            config: Configuration dictionary or object
        """
        self.model_path = model_path or os.environ.get("GC_MODEL_PATH")
        self.config = config
        self.running = False
        self.server_thread = None
        self._llama_instance = None
        self._validate_setup()
        logger.info(f"LlamaServer initialized with model: {self.model_path}")
        
    def _validate_setup(self):
        """Ensure the server is properly configured."""
        if not self.model_path:
            logger.error("No model path provided")
            raise ValueError("Model path must be provided via argument or GC_MODEL_PATH env variable")
        
        if not Path(self.model_path).exists():
            logger.error(f"Model file not found: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
    def _load_model(self):
        """Load the language model using llama-cpp-python."""
        try:
            # We'll use a dynamic import to avoid dependency issues if not installed
            from llama_cpp import Llama
            
            # Configure the model based on the hardware capabilities
            # Optimize for Intel i9-11900KF and AMD Radeon RX 580
            
            # For AMD GPU with ROCm backend
            gpu_layers = 0
            if self.config and self.config.get('use_gpu', True):
                gpu_layers = -1  # Use all layers on GPU if possible
                os.environ["GGML_OPENCL_PLATFORM"] = "AMD"
                os.environ["GGML_OPENCL_DEVICE"] = "0"  # Primary GPU
            
            # Configure number of threads based on CPU (i9-11900KF has 8 cores/16 threads)
            n_threads = (self.config and self.config.get('threads')) or 8
            
            # Initialize the model
            self._llama_instance = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get('context_size', 4096),
                n_threads=n_threads,
                n_gpu_layers=gpu_layers,
                seed=self.config.get('seed', 42),
                verbose=self.config.get('verbose', False)
            )
            
            logger.info(f"Model loaded successfully with {n_threads} threads and GPU layers: {gpu_layers}")
            return True
        except ImportError:
            logger.error("llama-cpp-python package not found. Please install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
        
    def start(self, host="0.0.0.0", port=8080):
        """Start the LlamaServer on the specified host and port."""
        if self.running:
            logger.warning("Server is already running")
            return False
            
        # Load the model
        if not self._load_model():
            return False
            
        # Start the server in a separate thread
        self.running = True
        self.server_thread = threading.Thread(
            target=self._server_loop, 
            args=(host, port), 
            daemon=True
        )
        self.server_thread.start()
        
        logger.info(f"Starting LlamaServer on {host}:{port}")
        logger.info("Server running. Press Ctrl+C to stop.")
        return True
        
    def _server_loop(self, host, port):
        """Main server loop."""
        # TODO: Implement actual server logic here
        # This would include setting up API endpoints, WebSocket, etc.
        while self.running:
            time.sleep(1)  # Placeholder for actual server logic
            
    def stop(self):
        """Stop the LlamaServer."""
        if not self.running:
            logger.warning("Server is not running")
            return
            
        logger.info("Stopping LlamaServer")
        self.running = False
        
        if self.server_thread:
            self.server_thread.join(timeout=5.0)
            
        # Clean up llama instance
        self._llama_instance = None
        logger.info("Server stopped")
        
    def generate(self, prompt, max_tokens=256, temperature=0.7, top_p=0.95, stream=False):
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stream: Whether to stream the results
            
        Returns:
            Generated text or generator if streaming
        """
        if not self._llama_instance:
            logger.error("Model not loaded, call start() first")
            return None
            
        logger.debug(f"Generating with prompt: {prompt[:50]}...")
        
        try:
            if stream:
                return self._generate_stream(prompt, max_tokens, temperature, top_p)
            else:
                return self._generate_sync(prompt, max_tokens, temperature, top_p)
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None
    
    def _generate_sync(self, prompt, max_tokens, temperature, top_p):
        """Synchronous generation."""
        result = self._llama_instance.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=40,
            repeat_penalty=1.1
        )
        return result["choices"][0]["text"]
    
    def _generate_stream(self, prompt, max_tokens, temperature, top_p):
        """Streaming generation."""
        for token in self._llama_instance.create_completion(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=40,
            repeat_penalty=1.1,
            stream=True
        ):
            yield token["choices"][0]["text"]