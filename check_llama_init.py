#!/usr/bin/env python
"""
Script to check and optimize system for running llama.cpp.
Executed on first launch or when hardware changes are detected.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add project to import path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.hardware_optimizer import HardwareOptimizer
from src.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('llama_init.log')
    ]
)

logger = logging.getLogger("check_llama_init")


def check_first_run() -> bool:
    """
    Checks if this is the first system run.
    
    Returns:
        bool: True if first run, False otherwise
    """
    # Check for hardware profile file
    hardware_profile_path = os.path.join("config", "hardware_profile.json")
    if not os.path.exists(hardware_profile_path):
        return True
    
    # Check for bin directory with compiled server
    bin_dir = os.path.join("bin")
    server_path = os.path.join(bin_dir, "llama-server")
    if platform.system() == "Windows":
        server_path += ".exe"
    
    if not os.path.exists(server_path):
        return True
    
    return False


def check_hardware_changes(optimizer: HardwareOptimizer) -> bool:
    """
    Checks for hardware changes.
    
    Args:
        optimizer: Initialized optimizer
    
    Returns:
        bool: True if changes detected, False otherwise
    """
    return optimizer._is_profile_outdated()


def perform_optimization(quiet: bool = False, force: bool = False) -> bool:
    """
    Performs system optimization if necessary.
    
    Args:
        quiet: Suppress output
        force: Force optimization
    
    Returns:
        bool: True if optimization successful, False otherwise
    """
    try:
        optimizer = HardwareOptimizer()
        
        # Check if optimization needed
        is_first_run = check_first_run()
        has_hardware_changes = check_hardware_changes(optimizer)
        
        if is_first_run or has_hardware_changes or force:
            if not quiet:
                if is_first_run:
                    logger.info("First system run. Performing initial optimization.")
                elif has_hardware_changes:
                    logger.info("Hardware changes detected. Performing re-optimization.")
                else:
                    logger.info("Force optimization.")
            
            # Load configuration
            config = load_config()
            
            # Update hardware profile
            optimizer._update_hardware_profile()
            
            # Optimize launch parameters
            optimizer.optimize_compilation_flags()
            optimizer.optimize_runtime_parameters()
            
            # If model available, run benchmarking
            if os.path.exists(config.model_path):
                if not quiet:
                    logger.info(f"Running benchmark on model: {config.model_path}")
                
                try:
                    optimizer.run_benchmark(config.model_path, iterations=1)
                except Exception as e:
                    if not quiet:
                        logger.warning(f"Failed to run benchmarking: {e}")
            
            # If server not compiled yet, try to build it
            bin_dir = os.path.join("bin")
            server_path = os.path.join(bin_dir, "llama-server")
            if platform.system() == "Windows":
                server_path += ".exe"
            
            if not os.path.exists(server_path):
                if not quiet:
                    logger.info("Server not found. Attempting to compile.")
                
                try:
                    # Server compilation (may take a while!)
                    compile_success = optimizer.compile_optimized_server()
                    
                    if not quiet:
                        if compile_success:
                            logger.info("Server compiled successfully.")
                        else:
                            logger.warning("Failed to compile server.")
                except Exception as e:
                    if not quiet:
                        logger.warning(f"Server compilation error: {e}")
            
            return True
        else:
            if not quiet:
                logger.info("System already optimized.")
            return True
            
    except Exception as e:
        if not quiet:
            logger.error(f"System optimization error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Check and optimize system for running llama.cpp"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Suppress message output"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force optimization"
    )
    
    args = parser.parse_args()
    
    success = perform_optimization(args.quiet, args.force)
    
    return 0 if success else 1


if __name__ == "__main__":
    import platform
    sys.exit(main())