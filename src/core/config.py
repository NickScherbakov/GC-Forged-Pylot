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
    # Model settings
    model_path: str = ""
    model_type: str = "llama"  # llama, alpaca, wizard, etc.
    context_size: int = 4096
    
    # Hardware settings
    use_gpu: bool = True
    gpu_layers: int = -1  # -1 means all layers to GPU if possible
    threads: int = 8
    batch_size: int = 512
    
    # Generation settings
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    seed: int = 42
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    api_key: str = ""
    
    # Hardware profile (auto-detected)
    hardware_profile: HardwareProfile = field(default_factory=HardwareProfile)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LlamaConfig':
        """Create from dictionary."""
        config_data = data.copy()
        
        # Handle nested hardware profile
        if "hardware_profile" in config_data and isinstance(config_data["hardware_profile"], dict):
            hardware_data = config_data.pop("hardware_profile")
            config = cls(**config_data)
            config.hardware_profile = HardwareProfile(**hardware_data)
            return config
        
        return cls(**config_data)
    
    def save(self, config_path: str) -> None:
        """Save configuration to file."""
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
    
    def optimize_for_hardware(self) -> None:
        """Optimize settings based on detected hardware."""
        self.detect_hardware()
        
        # CPU optimization
        if "i9-11900" in self.hardware_profile.cpu_model:
            # Intel i9-11900KF optimization
            self.threads = min(8, self.hardware_profile.cpu_threads // 2)
            logger.info(f"Optimized for Intel i9-11900KF with {self.threads} threads")
        else:
            # Generic optimization: use half of available threads
            self.threads = max(1, self.hardware_profile.cpu_threads // 2)
        
        # GPU optimization
        if self.hardware_profile.has_amd_gpu:
            if "RX 580" in self.hardware_profile.gpu_model:
                # RX 580 has 4GB VRAM, adjust accordingly
                self.gpu_layers = 24  # Conservative setting for 4GB VRAM
                self.context_size = 2048  # Reduce context for better performance
                logger.info("Optimized for AMD RX 580 with 4GB VRAM")
            elif self.hardware_profile.gpu_vram > 6000:
                # More capable AMD GPU
                self.gpu_layers = -1  # Use all layers
            else:
                # Limited VRAM
                self.gpu_layers = 12  # Very conservative
        
        # Adjust batch size based on available RAM
        if self.hardware_profile.total_ram > 32000:  # More than 32GB
            self.batch_size = 1024
        elif self.hardware_profile.total_ram > 16000:  # More than 16GB
            self.batch_size = 512
        else:
            self.batch_size = 256
        
        logger.info(f"Configuration optimized for detected hardware")
    
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


def cpuinfo() -> Dict[str, Any]:
    """Get CPU information."""
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for cpu in c.Win32_Processor():
                return {"brand_raw": cpu.Name}
        except:
            pass
    
    # Fallback to platform info
    return {"brand_raw": platform.processor() or "Unknown CPU"}


def load_config(config_path: Optional[str] = None) -> LlamaConfig:
    """
    Load configuration from file or create default.
    
    Args:
        config_path: Path to config file
        
    Returns:
        LlamaConfig object
    """
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            config = LlamaConfig.from_dict(config_data)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    # Create default config
    config = LlamaConfig()
    config.optimize_for_hardware()
    
    # Set model path to environment variable if exists
    if os.environ.get("GC_MODEL_PATH"):
        config.model_path = os.environ.get("GC_MODEL_PATH")
    
    if config_path:
        config.save(config_path)
        
    return config


def get_default_model_path() -> str:
    """Get default model path."""
    # Check environment variable first
    if os.environ.get("GC_MODEL_PATH"):
        return os.environ.get("GC_MODEL_PATH")
    
    # Check standard locations
    base_dirs = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models"),
        os.path.join(os.path.expanduser("~"), "gc-forged-pylot", "models"),
        os.path.join(os.environ.get("APPDATA", ""), "gc-forged-pylot", "models") if platform.system() == "Windows" else None
    ]
    
    model_extensions = [".gguf", ".bin"]
    
    for base_dir in filter(None, base_dirs):
        if os.path.exists(base_dir):
            for ext in model_extensions:
                models = list(Path(base_dir).glob(f"*{ext}"))
                if models:
                    return str(models[0])
    
    return ""