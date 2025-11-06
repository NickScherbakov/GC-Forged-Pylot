"""
GC-Core: Optimized llama.cpp server with enhancements for IDE integration.
"""

__version__ = "0.1.0"

from .server import LlamaServer
from .config import LlamaConfig, load_config