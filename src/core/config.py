"""
Configuration management for GC-Forged-Pylot.
Optimized for specific hardware configurations.
"""
import os
import json
import logging
import platform
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class HardwareProfile:
    """Hardware profile information."""
    cpu_model: str = "Unknown"
    cpu_cores: int = 1
    cpu_threads: int = 1
    cpu_speed: float = 0.0  # GHz
    gpu_model: str = "Unknown"
    gpu_vram: int = 0  # MB
    total_ram: int = 0  # MB
    has_amd_gpu: bool = False
    has_nvidia_gpu: bool = False
    has_rocm: bool = False
    has_cuda: bool = False

@dataclass
class LlamaConfig:
    """Configuration for the Llama server and model."""
    n_ctx: int = 2048
    n_batch: int = 512
    n_gpu_layers: int = 0
    n_threads: int = 4
    embedding: bool = True
    model_path: str = field(default_factory=lambda: get_default_model_path())
    model_vram_gb: float = 6.0
    stop_words: List[str] = field(default_factory=list)
    port: int = 8080
    host: str = "127.0.0.1"
    hardware_profile: HardwareProfile = field(default_factory=HardwareProfile)
    tensor_split: List[float] = field(default_factory=list)
    
    def detect_hardware(self) -> None:
        """Detect and populate hardware information."""
        profile = self.hardware_profile
        
        # CPU detection
        try:
            cpu_info = cpuinfo()
            profile.cpu_model = cpu_info.get("brand_raw", "Unknown CPU")
            profile.cpu_cores = psutil.cpu_count(logical=False) or 1
            profile.cpu_threads = psutil.cpu_count(logical=True) or 1
            
            # Try to extract CPU speed
            if "GHz" in profile.cpu_model:
                try:
                    ghz_part = profile.cpu_model.split("@")[1].strip().split("GHz")[0].strip()
                    profile.cpu_speed = float(ghz_part)
                except (IndexError, ValueError):
                    profile.cpu_speed = 0.0
            
            logger.info(f"Detected CPU: {profile.cpu_model} ({profile.cpu_cores} cores, {profile.cpu_threads} threads)")
        except Exception as e:
            logger.warning(f"Failed to detect CPU info: {e}")
        
        # RAM detection
        try:
            mem_info = psutil.virtual_memory()
            profile.total_ram = mem_info.total // (1024 * 1024)  # Convert to MB
            logger.info(f"Detected RAM: {profile.total_ram} MB")
        except Exception as e:
            logger.warning(f"Failed to detect RAM info: {e}")
        
        # GPU detection
        profile.has_amd_gpu, profile.has_nvidia_gpu = False, False
        profile.has_rocm, profile.has_cuda = False, False
        
        # Attempt Windows GPU detection using WMI
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if "AMD" in gpu.Name or "Radeon" in gpu.Name:
                        profile.has_amd_gpu = True
                        profile.gpu_model = gpu.Name
                        # Rough VRAM estimation
                        try:
                            if hasattr(gpu, 'AdapterRAM'):
                                profile.gpu_vram = int(gpu.AdapterRAM) // (1024 * 1024)
                        except:
                            pass
                    elif "NVIDIA" in gpu.Name:
                        profile.has_nvidia_gpu = True
                        profile.gpu_model = gpu.Name
                        # Rough VRAM estimation
                        try:
                            if hasattr(gpu, 'AdapterRAM'):
                                profile.gpu_vram = int(gpu.AdapterRAM) // (1024 * 1024)
                        except:
                            pass
                    logger.info(f"Detected GPU: {profile.gpu_model} with {profile.gpu_vram} MB VRAM")
            except Exception as e:
                logger.warning(f"Failed to detect GPU using WMI: {e}")
                
                # Hardcode since we know the hardware
                if not profile.gpu_model or profile.gpu_model == "Unknown":
                    profile.has_amd_gpu = True
                    profile.gpu_model = "AMD Radeon RX 580 2048SP"
                    profile.gpu_vram = 4096  # 4GB VRAM
                    logger.info(f"Using hardcoded GPU info: {profile.gpu_model}")
        
        # Check for CUDA
        try:
            result = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                profile.has_cuda = True
                logger.info("CUDA detected")
        except:
            pass
        
        # Check for ROCm
        try:
            result = subprocess.run(["rocminfo"], capture_output=True, text=True)
            if result.returncode == 0:
                profile.has_rocm = True
                logger.info("ROCm detected")
        except:
            # On Windows, ROCm detection is complicated
            # Check if known AMD driver files exist
            if profile.has_amd_gpu and os.path.exists(os.path.join(os.environ.get("SystemDrive", "C:"), 
                                                                  "Windows", "System32", "amdocl.dll")):
                profile.has_rocm = True
                logger.info("AMD OCL detected, assuming ROCm compatibility")

    def optimize_for_hardware(self) -> None:
        """Optimize configuration based on detected hardware."""
        # First ensure hardware is detected
        if not self.hardware_profile.cpu_model or self.hardware_profile.cpu_model == "Unknown":
            self.detect_hardware()
        
        # Use hardware optimizer for advanced optimization
        try:
            from .hardware_optimizer import HardwareOptimizer
            optimizer = HardwareOptimizer()
            
            # Check if this is the first run or if hardware profile has changed
            if optimizer._is_profile_outdated():
                logger.info("Hardware profile outdated or not present. Running optimization...")
                # Use the model path for benchmarking if available
                if os.path.exists(self.model_path):
                    optimizer.run_optimization(self.model_path)
                else:
                    # Still update hardware profile without running benchmark
                    optimizer._update_hardware_profile()
                    optimizer.optimize_compilation_flags()
                    optimizer.optimize_runtime_parameters()
            
            # Apply optimized parameters to config
            params = optimizer.get_optimal_launch_parameters()
            self.n_threads = params.get("threads", self.n_threads)
            self.n_ctx = params.get("n_ctx", self.n_ctx)
            self.n_batch = params.get("batch_size", self.n_batch)
            self.n_gpu_layers = params.get("n_gpu_layers", self.n_gpu_layers)
            self.tensor_split = params.get("tensor_split", self.tensor_split)
            
            logger.info(f"Applied optimized parameters: threads={self.n_threads}, " +
                      f"n_ctx={self.n_ctx}, batch={self.n_batch}, gpu_layers={self.n_gpu_layers}")
            
        except ImportError:
            # Fall back to basic optimization if hardware_optimizer is not available
            self._basic_hardware_optimization()
    
    def _basic_hardware_optimization(self) -> None:
        """Basic optimization based on detected hardware (fallback)."""
        profile = self.hardware_profile
        
        # Optimize thread count
        self.n_threads = min(profile.cpu_cores, max(4, profile.cpu_cores - 1))
        
        # GPU layers
        if profile.has_nvidia_gpu and profile.has_cuda:
            if profile.gpu_vram >= 8000:
                self.n_gpu_layers = 32
            elif profile.gpu_vram >= 4000:
                self.n_gpu_layers = 20
            elif profile.gpu_vram > 0:
                self.n_gpu_layers = 8
        elif profile.has_amd_gpu and profile.has_rocm:
            if profile.gpu_vram >= 8000:
                self.n_gpu_layers = 28
            elif profile.gpu_vram >= 4000:
                self.n_gpu_layers = 16
            elif profile.gpu_vram > 0:
                self.n_gpu_layers = 4
            
        # Context size based on RAM
        if profile.total_ram > 32000:
            self.n_ctx = 4096
        elif profile.total_ram > 16000:
            self.n_ctx = 2048
        else:
            self.n_ctx = 1024
            
        # Batch size
        if profile.total_ram > 16000:
            self.n_batch = 512
        else:
            self.n_batch = 256

        logger.info(f"Applied basic optimization: threads={self.n_threads}, " +
                  f"n_ctx={self.n_ctx}, batch={self.n_batch}, gpu_layers={self.n_gpu_layers}")

def cpuinfo() -> Dict[str, Any]:
    """Get CPU information."""
    info = {}
    
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                info["brand_raw"] = cpu.Name
                break
        except:
            # Fallback to platform
            info["brand_raw"] = platform.processor()
    elif platform.system() == "Linux":
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.strip():
                        if line.rstrip('\n').startswith('model name'):
                            info["brand_raw"] = line.rstrip('\n').split(':')[1].strip()
                            break
        except:
            info["brand_raw"] = platform.processor()
    else:  # Darwin/macOS
        try:
            import subprocess
            output = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode('utf-8').strip()
            info["brand_raw"] = output
        except:
            info["brand_raw"] = platform.processor()
            
    if not info.get("brand_raw"):
        info["brand_raw"] = platform.processor() or "Unknown CPU"
        
    return info


def load_config(config_path: Optional[str] = None) -> LlamaConfig:
    """Load configuration from file or use defaults."""
    config = LlamaConfig()
    
    if not config_path:
        config_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "llama_config.json"),
            os.path.expanduser("~/.gcforgedpylot/config.json")
        ]
    else:
        config_paths = [config_path]
    
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    config_dict = json.load(f)
                
                # Update config from file
                for key, value in config_dict.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                logger.info(f"Loaded configuration from {path}")
                break
            except Exception as e:
                logger.error(f"Failed to load config from {path}: {e}")
    
    # Always do hardware detection and optimization
    config.detect_hardware()
    config.optimize_for_hardware()
    
    return config


def get_default_model_path() -> str:
    """Get default model path."""
    # Try to find a model in the models directory
    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "models")
    
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith('.gguf')]
        if model_files:
            return os.path.join(models_dir, model_files[0])
    
    # Default to a well-known model
    return os.path.join(models_dir, "tinyllama-1.1b-chat-v1.0.Q2_K.gguf")