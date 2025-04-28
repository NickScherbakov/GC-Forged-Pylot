"""
GC-Core: Оптимизированный llama.cpp сервер с улучшениями для интеграции с IDE.
"""

__version__ = "0.1.0"

from .server import LlamaServer
from .config import LlamaConfig, load_config