#!/usr/bin/env python3
"""
GC-Forged-Pylot - Application Entry Point
Launches local LLM server based on llama.cpp with GitHub Copilot integration

Author: GC-Forged-Pylot Team
"""
import argparse
import uvicorn
import logging
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Remove the unused import
# from src.core.api import LlamaAPI 
from src.core.server import LlamaServer
from src.core.config_loader import load_config
from check_llama_init import perform_optimization

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(), logging.FileHandler("pylot_agent.log")])
logger = logging.getLogger(__name__)

def main():
    load_dotenv() # Load environment variables from .env file

    parser = argparse.ArgumentParser(description="Run the Llama Server")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the configuration file")
    parser.add_argument("--host", type=str, default=None, help="Host to bind the server to (overrides config)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind the server to (overrides config)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--skip-optimization", action="store_true", help="Skip hardware optimization")
    parser.add_argument("--force-optimization", action="store_true", help="Force hardware optimization")
    # Add other relevant arguments from config if needed for overrides

    args = parser.parse_args()

    try:
        # Check and optimize system if necessary
        if not args.skip_optimization:
            logger.info("Checking system optimization...")
            optimization_result = perform_optimization(quiet=False, force=args.force_optimization)
            if not optimization_result:
                logger.warning("System optimization check failed. Continuing anyway.")
        else:
            logger.info("System optimization check skipped.")

        config = load_config(args.config)
        logger.info(f"Configuration loaded from {args.config}")

        # Override config with command-line arguments if provided
        server_config = config.get('server', {})
        host = args.host or server_config.get('host', '127.0.0.1')
        port = args.port or server_config.get('port', 8000)

        model_config = config.get('model', {})
        cache_config = config.get('cache', {})
        api_keys = config.get('api_keys', []) # Load API keys from config

        # Load optimized parameters if available
        try:
            from src.core.hardware_optimizer import HardwareOptimizer
            optimizer = HardwareOptimizer()
            optimized_params = optimizer.get_optimal_launch_parameters()
            
            # Update parameters from optimized profile if not explicitly specified in config
            if 'n_ctx' not in model_config:
                model_config['n_ctx'] = optimized_params.get('n_ctx', 2048)
            if 'n_gpu_layers' not in model_config:
                model_config['n_gpu_layers'] = optimized_params.get('n_gpu_layers', 0)
            if 'n_threads' not in model_config:
                model_config['n_threads'] = optimized_params.get('threads', 4)
            if 'tensor_split' not in model_config and optimized_params.get('tensor_split'):
                model_config['tensor_split'] = optimized_params.get('tensor_split')
                
            logger.info(f"Using optimized parameters: n_ctx={model_config['n_ctx']}, " +
                      f"n_gpu_layers={model_config['n_gpu_layers']}, n_threads={model_config['n_threads']}")
        except Exception as e:
            logger.warning(f"Could not load optimized parameters: {e}")

        # Initialize the LlamaServer
        llama_server = LlamaServer(
            model_path=model_config.get('path'),
            n_ctx=model_config.get('n_ctx', 2048),
            n_gpu_layers=model_config.get('n_gpu_layers', 0),
            n_threads=model_config.get('n_threads', 4),
            tensor_split=model_config.get('tensor_split', []),
            verbose=server_config.get('verbose', False),
            cache_config=cache_config,
            api_keys=api_keys # Pass API keys
            # Pass other necessary parameters from config to LlamaServer constructor
        )
        
        # Explicitly load model before getting FastAPI app
        logger.info("Loading the LLM model...")
        if not llama_server._load_model():
            logger.error("Failed to load the model. Exiting.")
            return

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