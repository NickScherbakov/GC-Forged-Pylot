#!/usr/bin/env python
"""
Script to optimize llama.cpp for specific hardware.
Analyzes hardware, compiles optimized server version,
and creates a profile of optimal launch parameters.
"""
import os
import sys
import argparse
import logging
import time
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
        logging.FileHandler('optimize_llama.log')
    ]
)

logger = logging.getLogger("optimize_llama")


def main():
    parser = argparse.ArgumentParser(
        description="Optimize llama.cpp for specific hardware"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        help="Path to model file for benchmarking"
    )
    parser.add_argument(
        "--compile", 
        action="store_true", 
        help="Compile optimized server version"
    )
    parser.add_argument(
        "--benchmark", 
        action="store_true", 
        help="Run benchmark"
    )
    parser.add_argument(
        "--llama-cpp", 
        type=str, 
        help="Path to llama.cpp sources"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        help="Text for benchmark", 
        default="Explain the theory of relativity in simple terms."
    )
    parser.add_argument(
        "--iterations", 
        type=int, 
        help="Number of benchmark iterations", 
        default=3
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force optimization even if profile is current"
    )
    parser.add_argument(
        "--skip-compilation", 
        action="store_true", 
        help="Skip server compilation stage (for systems without development tools)"
    )
    
    args = parser.parse_args()
    
    # Initialize optimizer
    optimizer = HardwareOptimizer()
    
    if args.force:
        # Force create new profile when running with --force
        logger.info("Force creating new optimization profile")
        optimizer._create_new_profile()
    
    # Determine model path
    model_path = args.model
    if not model_path:
        # If path not specified, try loading from config
        config = load_config()
        model_path = config.model_path
        
        if not os.path.exists(model_path):
            logger.warning(f"Модель не найдена по пути {model_path}")
            model_path = None
    
    if args.compile or (args.model is None and not args.benchmark):
        # Compile optimized server version
        if args.skip_compilation:
            logger.info("Compilation stage skipped (--skip-compilation)")
        else:
            logger.info("Starting optimized server compilation")
            start_time = time.time()
            success = optimizer.compile_optimized_server(args.llama_cpp)
            
            if success:
                logger.info(f"Server compiled successfully in {time.time() - start_time:.1f} sec")
            else:
                logger.error("Failed to compile server")
                return 1
    
    if args.benchmark and model_path:
        # Run benchmark
        logger.info(f"Running benchmark on model: {model_path}")
        start_time = time.time()
        
        if args.skip_compilation:
            # Use mock benchmark if server unavailable
            logger.info("Using mock benchmark (--skip-compilation)")
            result = optimizer.run_mock_benchmark(
                model_path=model_path,
                prompt=args.prompt,
                iterations=args.iterations
            )
        else:
            # Use real benchmark
            result = optimizer.run_benchmark(
                model_path=model_path,
                prompt=args.prompt,
                iterations=args.iterations
            )
        
        logger.info(f"Benchmark completed in {time.time() - start_time:.1f} sec")
        logger.info(f"Results: {result.tokens_per_second:.2f} токенов/sec, "
                  f"latency: {result.latency_ms:.2f} ms")
    else:
        # Simply update hardware profile and parameters
        if model_path:
            # Full optimization with benchmarking
            logger.info("Starting full optimization with benchmarking")
            results = optimizer.run_optimization(model_path)
            logger.info(f"Optimization complete. Optimal launch parameters:")
            logger.info(f"- Threads: {results['runtime_parameters']['n_threads']}")
            logger.info(f"- Context: {results['runtime_parameters']['n_ctx']}")
            logger.info(f"- Batch size: {results['runtime_parameters']['batch_size']}")
            logger.info(f"- GPU layers: {results['runtime_parameters']['n_gpu_layers']}")
        else:
            # Optimization without benchmarking
            logger.info("Starting optimization without benchmarking (model path not specified)")
            optimizer._update_hardware_profile()
            compilation_flags = optimizer.optimize_compilation_flags()
            runtime_params = optimizer.optimize_runtime_parameters()
            
            logger.info("Optimization complete. Estimated optimal parameters:")
            logger.info(f"- Threads: {runtime_params.n_threads}")
            logger.info(f"- Context: {runtime_params.n_ctx}")
            logger.info(f"- Batch size: {runtime_params.batch_size}")
            logger.info(f"- GPU layers: {runtime_params.n_gpu_layers}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())