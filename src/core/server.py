
## 2️⃣ src/core/server.py

```python
"""/core/config.py

```python name=
Core server implementation that interfaces with llama.cpp.
"""
import os
import sys
import loggingsrc/core/config.py
"""
Configuration management for GC-Core.
"""
import os
import json
from pathlib import Path
from dataclasses import data
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LlamaServer:
    class
from typing import Dict, Any, Optional, List

@dataclass
class LlamaConfig:
    """Configuration for the Llama"""
    A wrapper around llama.cpp that provides enhanced functionality
    for IDE integration and continuous operation.
    """
    
    def __init__(self, model_path=None, config=Server."""
    model_path: str
    context_size: int = 4096
    threads: int = 4
    batch_size: intNone):
        """
        Initialize the LlamaServer with model path and configuration.
        
        Args:
            model_path: Path to the  = 512
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LlamaConfig':
        """Create a LlamaConfig from a dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            "model_path": self.model_path,
            "context_sizeGGUF model file
            config: Configuration dictionary or object
        """
        self.model_path = model_path or os.environ.get("GC_MODEL_PATH")
        self.config = config
        self._validate_setup()
        logger.info(f"LlamaServer initialized with model: {self.model_path}")
        
    def _validate_setup(self):
        """Validate that the model exists and other requirements are met."""
        if not self.model_path:
            logger.error("No model path provided via argument or GC_MODEL_PATH environment variable")
            raise ValueError("Model path must be specified")
            
        model_file = Path(self.model_path": self.context_size,
            "threads": self.threads,
            "batch_size": self)
        if not model_file.exists():
            logger.error(f"Model file not found: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
    
    def start.batch_size,
            "temperature": self.temperature,
            "top_p(self):
        """Start the llama.cpp server": self.top_p,
            "top_k": self.top_k, process."""
        logger.info("Starting LlamaServer...")
        # TODO
            "repeat_penalty": self.repeat_penalty,
        }

def load_config(config_path: Optional[str] =: Implement actual llama.cpp process start
        
    def stop(self):
        """ None) -> LlamaConfig:
    """
    Load configuration from the specified path or default locations.
    
    Args:
        config_path: Path to the configurationStop the llama.cpp server process."""
        logger.info("Stopping LlamaServer...")
         file
        
    Returns:
        LlamaConfig object
    """
    # Default config paths to check
    default_paths = [
        Path("# TODO: Implement actual llama.cpp process stop
        
    def query(self, promptconfig.json"),
        Path., params=None):
        """
        Send a query to the llama.cpp server.
        
        Args:
            prompt: The text prompt to send
            params: Additional parameters for the query
            
        Returns:home() / ".gc-forged-pyl
            The model's response as a string
        """
        logger.info(f"Sending query, length: {len(prompt)} chars")
        #ot" / "config.json",
        Path("/etc/gc-forged-pylot/config.json"),
    ] TODO: Implement actual query to llama.cpp
        return f"Response to: {prompt[:30]}..."

def main():
    """Main entry point for command-line usage."""
    server = Llama
    
    # Add user-specified path if provided
    paths_to_check = [Path(config_path)] if config_path else default_paths
    
    # Check for existing config file
    config_file = NoneServer()
    server.start()
    
if __name__ == "__main__":
    main()