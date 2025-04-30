#!/usr/bin/env python3
"""
GC-Forged-Pylot - Точка входа в приложение
Запускает локальный LLM сервер на базе llama.cpp с интеграцией GitHub Copilot

Автор: GC-Forged-Pylot Team
"""
import argparse
import uvicorn
import logging
from dotenv import load_dotenv
import os

# Remove the unused import
# from src.core.api import LlamaAPI 
from src.core.server import LlamaServer
from src.core.config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Run the Llama Server")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the configuration file")
    parser.add_argument("--host", type=str, default=None, help="Host to bind the server to (overrides config)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind the server to (overrides config)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    # Add other relevant arguments from config if needed for overrides

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        logger.info(f"Configuration loaded from {args.config}")

        # Override config with command-line arguments if provided
        server_config = config.get('server', {})
        host = args.host or server_config.get('host', '127.0.0.1')
        port = args.port or server_config.get('port', 8000)

        model_config = config.get('model', {})
        cache_config = config.get('cache', {})
        api_keys = config.get('api_keys', []) # Load API keys from config

        # Initialize the LlamaServer
        llama_server = LlamaServer(
            model_path=model_config.get('path'),
            n_ctx=model_config.get('n_ctx', 2048),
            n_gpu_layers=model_config.get('n_gpu_layers', 0),
            verbose=server_config.get('verbose', False),
            cache_config=cache_config,
            api_keys=api_keys # Pass API keys
            # Pass other necessary parameters from config to LlamaServer constructor
        )

        logger.info(f"Starting server on {host}:{port}")

        # Get the FastAPI app instance from the server
        app = llama_server.get_app()

        # Run the server using uvicorn
        uvicorn.run(
            app, # Use the app from LlamaServer
            host=host,
            port=port,
            reload=args.reload,
            log_level="info" # Or configure based on verbosity/debug flags
        )

    except FileNotFoundError:
        logger.error(f"Configuration file not found at {args.config}")
    except Exception as e:
        logger.error(f"Failed to start the server: {e}", exc_info=True) # Log traceback

if __name__ == "__main__":
    main()