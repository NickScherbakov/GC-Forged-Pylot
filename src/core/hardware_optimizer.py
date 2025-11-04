"""
Hardware Optimizer for GC-Forged-Pylot.
Analyzes hardware and optimizes llama.cpp parameters.
"""
import os
import json
import logging
import platform
import subprocess
import time
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field, asdict
import psutil
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from .config import HardwareProfile, LlamaConfig

logger = logging.getLogger(__name__)

@dataclass
class CompilationFlags:
    """Флаги компиляции для llama.cpp."""
    cmake_flags: List[str] = field(default_factory=list)
    make_flags: List[str] = field(default_factory=list)
    cpu_arch_flags: List[str] = field(default_factory=list)
    build_type: str = "Release"
    use_cuda: bool = False
    use_rocm: bool = False
    use_metal: bool = False
    use_vulkan: bool = False
    use_openmp: bool = True
    use_avx: bool = False
    use_avx2: bool = False
    use_avx512: bool = False
    use_f16c: bool = False
    use_fma: bool = False

@dataclass
class RuntimeParameters:
    """Параметры запуска llama.cpp сервера."""
    n_threads: int = 4
    n_gpu_layers: int = 0
    batch_size: int = 512
    context_size: int = 2048
    embedding_size: int = 4096
    keep_in_vram: bool = False
    tensor_split: List[float] = field(default_factory=list)
    n_ctx: int = 2048
    rope_freq_base: int = 10000
    rope_freq_scale: float = 1.0

@dataclass
class BenchmarkResult:
    """Результаты бенчмарка."""
    tokens_per_second: float = 0.0
    latency_ms: float = 0.0
    memory_used_mb: int = 0
    temperature_max: float = 0.0
    prompt: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationProfile:
    """Профиль оптимизации для конкретной системы."""
    hardware: HardwareProfile = field(default_factory=HardwareProfile)
    compilation_flags: CompilationFlags = field(default_factory=CompilationFlags)
    runtime_parameters: RuntimeParameters = field(default_factory=RuntimeParameters)
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

class HardwareOptimizer:
    """
    Анализирует оборудование и оптимизирует параметры запуска llama.cpp.
    """
    def __init__(self, config_path: Optional[str] = None):
        self.config = LlamaConfig()
        self.profile_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "config", "hardware_profile.json"
        )
        self.optimization_profile = OptimizationProfile()
        self._load_or_create_profile()
        
    def _load_or_create_profile(self) -> None:
        """Загружает существующий профиль или создает новый."""
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                # Восстанавливаем объекты из JSON
                self.optimization_profile = OptimizationProfile(
                    hardware=HardwareProfile(**profile_data.get("hardware", {})),
                    compilation_flags=CompilationFlags(**profile_data.get("compilation_flags", {})),
                    runtime_parameters=RuntimeParameters(**profile_data.get("runtime_parameters", {})),
                    benchmark_results=[BenchmarkResult(**r) for r in profile_data.get("benchmark_results", [])],
                    created_at=profile_data.get("created_at", ""),
                    updated_at=profile_data.get("updated_at", "")
                )
                logger.info(f"Загружен профиль оптимизации из {self.profile_path}")
                
                # Проверка актуальности профиля
                if self._is_profile_outdated():
                    logger.info("Профиль устарел, требуется переоптимизация")
                    self._update_hardware_profile()
            except Exception as e:
                logger.error(f"Ошибка загрузки профиля: {e}")
                self._create_new_profile()
        else:
            self._create_new_profile()
    
    def _create_new_profile(self) -> None:
        """Создает новый профиль оптимизации."""
        self.optimization_profile = OptimizationProfile(
            hardware=HardwareProfile(),
            compilation_flags=CompilationFlags(),
            runtime_parameters=RuntimeParameters(),
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        self._update_hardware_profile()
    
    def _is_profile_outdated(self) -> bool:
        """Проверяет, устарел ли профиль."""
        # Базовая проверка - профиль считается устаревшим, если:
        # 1. Изменилось количество доступной памяти (RAM/VRAM)
        # 2. Изменилась модель CPU/GPU
        # 3. Профилю больше месяца
        
        current_hw = HardwareProfile()
        self.config.detect_hardware()  # Используем существующую функцию для обновления current_hw
        current_hw = self.config.hardware_profile
        
        profile_hw = self.optimization_profile.hardware
        
        # Проверяем базовые характеристики
        if (abs(current_hw.total_ram - profile_hw.total_ram) > 1024 or  # Разница более 1 ГБ
            current_hw.cpu_model != profile_hw.cpu_model or
            current_hw.gpu_model != profile_hw.gpu_model or
            current_hw.has_cuda != profile_hw.has_cuda or
            current_hw.has_rocm != profile_hw.has_rocm):
            return True
        
        # Проверяем дату обновления
        try:
            last_updated = time.strptime(self.optimization_profile.updated_at, "%Y-%m-%d %H:%M:%S")
            days_since_update = (time.time() - time.mktime(last_updated)) / (60 * 60 * 24)
            if days_since_update > 30:  # Больше месяца
                return True
        except:
            return True
            
        return False
    
    def _update_hardware_profile(self) -> None:
        """Обновляет профиль оборудования с расширенным анализом."""
        # Сначала используем существующую функцию обнаружения оборудования
        self.config.detect_hardware()
        self.optimization_profile.hardware = self.config.hardware_profile
        
        # Дополним её расширенным анализом
        self._detect_cpu_features()
        self._detect_gpu_capabilities()
        
        self.optimization_profile.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_profile()
    
    def _detect_cpu_features(self) -> None:
        """Детектирует дополнительные возможности CPU."""
        cpu_profile = self.optimization_profile.hardware
        
        # Проверка поддержки AVX/AVX2/AVX512
        if platform.system() == "Windows":
            self._detect_cpu_features_windows()
        elif platform.system() == "Linux":
            self._detect_cpu_features_linux()
        elif platform.system() == "Darwin":
            self._detect_cpu_features_macos()
            
        logger.info(f"CPU features detected: " +
                   f"AVX={self.optimization_profile.compilation_flags.use_avx}, " +
                   f"AVX2={self.optimization_profile.compilation_flags.use_avx2}, " +
                   f"AVX512={self.optimization_profile.compilation_flags.use_avx512}, " +
                   f"FMA={self.optimization_profile.compilation_flags.use_fma}")
    
    def _detect_cpu_features_windows(self) -> None:
        """Обнаруживает расширения процессора на Windows."""
        try:
            # Попытка использовать PowerShell для получения информации о CPU
            cmd = ["powershell", "-Command", 
                  "[System.String]::Join(', ', (Get-WmiObject -Class Win32_Processor).Caption," +
                  "(Get-WmiObject -Class Win32_ProcessorFeature).Name)"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            features = result.stdout.lower()
            
            self.optimization_profile.compilation_flags.use_avx = 'avx' in features
            self.optimization_profile.compilation_flags.use_avx2 = 'avx2' in features
            self.optimization_profile.compilation_flags.use_avx512 = any(x in features for x in ['avx512', 'avx-512'])
            self.optimization_profile.compilation_flags.use_f16c = 'f16c' in features
            self.optimization_profile.compilation_flags.use_fma = 'fma' in features
        except Exception as e:
            logger.warning(f"Failed to detect CPU features on Windows: {e}")
            # Fallback to CPU model name matching
            cpu_model = self.optimization_profile.hardware.cpu_model.lower()
            
            # Примерное определение по названию процессора
            if any(x in cpu_model for x in ['ryzen', 'epyc', 'threadripper']):
                self.optimization_profile.compilation_flags.use_avx = True
                self.optimization_profile.compilation_flags.use_avx2 = True
                if '3' in cpu_model or '5' in cpu_model or '7' in cpu_model or '9' in cpu_model:
                    self.optimization_profile.compilation_flags.use_fma = True
                
            if any(x in cpu_model for x in ['i9', 'i7-8', 'i7-9', 'i7-10', 'i7-11', 'i7-12']):
                self.optimization_profile.compilation_flags.use_avx = True
                self.optimization_profile.compilation_flags.use_avx2 = True
                self.optimization_profile.compilation_flags.use_fma = True
                
            # Проверка на поддержку AVX-512 (обычно в Intel Ice Lake, Tiger Lake, Rocket Lake и новее)
            if any(x in cpu_model for x in ['xeon', 'i9-10', 'i9-11', 'i7-11', 'i5-11']):
                self.optimization_profile.compilation_flags.use_avx512 = True
    
    def _detect_cpu_features_linux(self) -> None:
        """Обнаруживает расширения процессора на Linux."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            flags_match = re.search(r'flags\s*:\s*(.*)', cpuinfo)
            if flags_match:
                flags = flags_match.group(1).lower()
                
                self.optimization_profile.compilation_flags.use_avx = 'avx' in flags
                self.optimization_profile.compilation_flags.use_avx2 = 'avx2' in flags
                self.optimization_profile.compilation_flags.use_avx512 = any(x in flags for x in ['avx512f', 'avx512vl'])
                self.optimization_profile.compilation_flags.use_f16c = 'f16c' in flags
                self.optimization_profile.compilation_flags.use_fma = 'fma' in flags
        except Exception as e:
            logger.warning(f"Failed to detect CPU features on Linux: {e}")
    
    def _detect_cpu_features_macos(self) -> None:
        """Обнаруживает расширения процессора на macOS."""
        try:
            result = subprocess.run(['sysctl', '-a'], capture_output=True, text=True)
            sysctl_output = result.stdout.lower()
            
            # Проверка на Apple Silicon
            if 'machdep.cpu.brand_string: apple' in sysctl_output:
                # Apple Silicon не имеет AVX, но имеет свои векторные расширения
                self.optimization_profile.compilation_flags.use_metal = True
                return
            
            # Проверка на Intel Mac
            self.optimization_profile.compilation_flags.use_avx = 'hw.optional.avx1_0: 1' in sysctl_output
            self.optimization_profile.compilation_flags.use_avx2 = 'hw.optional.avx2_0: 1' in sysctl_output
            self.optimization_profile.compilation_flags.use_avx512 = 'hw.optional.avx512f: 1' in sysctl_output
            self.optimization_profile.compilation_flags.use_fma = 'hw.optional.fma: 1' in sysctl_output
        except Exception as e:
            logger.warning(f"Failed to detect CPU features on macOS: {e}")
    
    def _detect_gpu_capabilities(self) -> None:
        """Определяет расширенные возможности GPU."""
        gpu_profile = self.optimization_profile.hardware
        
        # Улучшенное определение GPU на Windows
        if platform.system() == "Windows":
            try:
                # Сначала пробуем через WMI
                self._detect_gpu_windows_wmi()
                
                # Если не удалось, пробуем через командную строку
                if gpu_profile.gpu_model == "Unknown" or gpu_profile.gpu_vram == 0:
                    self._detect_gpu_windows_cmd()
            except Exception as e:
                logger.warning(f"Failed to detect GPU capabilities on Windows: {e}")
                # Запасной вариант: предположения на основе имени процессора
                self._fallback_gpu_detection()
        elif platform.system() == "Linux":
            try:
                self._detect_gpu_linux()
            except Exception as e:
                logger.warning(f"Failed to detect GPU capabilities on Linux: {e}")
                self._fallback_gpu_detection()
        elif platform.system() == "Darwin":
            try:
                self._detect_gpu_macos()
            except Exception as e:
                logger.warning(f"Failed to detect GPU capabilities on macOS: {e}")
                self._fallback_gpu_detection()
    
    def _detect_gpu_windows_wmi(self) -> None:
        """Определяет GPU через WMI на Windows."""
        try:
            import wmi
            c = wmi.WMI()
            for gpu in c.Win32_VideoController():
                if "AMD" in gpu.Name or "Radeon" in gpu.Name:
                    self.optimization_profile.hardware.has_amd_gpu = True
                    self.optimization_profile.hardware.gpu_model = gpu.Name
                    # Rough VRAM estimation
                    try:
                        if hasattr(gpu, 'AdapterRAM'):
                            vram = int(gpu.AdapterRAM) // (1024 * 1024)
                            if vram > 0:
                                self.optimization_profile.hardware.gpu_vram = vram
                    except:
                        pass
                    logger.info(f"Detected AMD GPU: {self.optimization_profile.hardware.gpu_model}")
                elif "NVIDIA" in gpu.Name:
                    self.optimization_profile.hardware.has_nvidia_gpu = True
                    self.optimization_profile.hardware.gpu_model = gpu.Name
                    # Rough VRAM estimation
                    try:
                        if hasattr(gpu, 'AdapterRAM'):
                            vram = int(gpu.AdapterRAM) // (1024 * 1024)
                            if vram > 0:
                                self.optimization_profile.hardware.gpu_vram = vram
                    except:
                        pass
                    logger.info(f"Detected NVIDIA GPU: {self.optimization_profile.hardware.gpu_model}")
                elif "Intel" in gpu.Name:
                    self.optimization_profile.hardware.gpu_model = gpu.Name
                    # Rough VRAM estimation for Intel GPUs
                    try:
                        if hasattr(gpu, 'AdapterRAM'):
                            vram = int(gpu.AdapterRAM) // (1024 * 1024)
                            if vram > 0:
                                self.optimization_profile.hardware.gpu_vram = vram
                    except:
                        pass
                    logger.info(f"Detected Intel GPU: {self.optimization_profile.hardware.gpu_model}")
        except ImportError:
            logger.warning("WMI library not available. Cannot detect GPU details via WMI.")
            raise
    
    def _detect_gpu_windows_cmd(self) -> None:
        """Определяет GPU через командную строку на Windows."""
        try:
            # PowerShell approach for GPU detection
            cmd = ["powershell", "-Command", "Get-WmiObject Win32_VideoController | Select-Object Name, AdapterRAM"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                # Parse the output
                import re
                
                # Look for GPU name
                name_match = re.search(r'Name\s*:\s*(.*)', output)
                if name_match:
                    gpu_name = name_match.group(1).strip()
                    self.optimization_profile.hardware.gpu_model = gpu_name
                    
                    if "AMD" in gpu_name or "Radeon" in gpu_name:
                        self.optimization_profile.hardware.has_amd_gpu = True
                    elif "NVIDIA" in gpu_name:
                        self.optimization_profile.hardware.has_nvidia_gpu = True
                
                # Look for VRAM
                vram_match = re.search(r'AdapterRAM\s*:\s*(\d+)', output)
                if vram_match:
                    vram = int(vram_match.group(1))
                    self.optimization_profile.hardware.gpu_vram = vram // (1024 * 1024)
                
                logger.info(f"Detected GPU via PowerShell: {self.optimization_profile.hardware.gpu_model} with {self.optimization_profile.hardware.gpu_vram} MB VRAM")
                
                # Try to detect graphics APIs
                self._detect_graphics_apis_windows()
        except Exception as e:
            logger.warning(f"Failed to detect GPU via command line: {e}")
            raise
    
    def _detect_graphics_apis_windows(self) -> None:
        """Определяет поддерживаемые графические API на Windows."""
        # Check for CUDA
        try:
            # Check for the nvcc compiler (part of CUDA toolkit)
            nvcc_cmd = ["where", "nvcc"]
            nvcc_result = subprocess.run(nvcc_cmd, capture_output=True, text=True)
            
            if nvcc_result.returncode == 0 and nvcc_result.stdout.strip():
                self.optimization_profile.hardware.has_cuda = True
                logger.info("CUDA detected (nvcc found)")
            else:
                # Try checking for NVIDIA DLLs
                if os.path.exists(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "nvcuda.dll")):
                    self.optimization_profile.hardware.has_cuda = True
                    logger.info("CUDA detected (nvcuda.dll found)")
        except Exception as e:
            logger.warning(f"Failed to check for CUDA: {e}")
        
        # Check for ROCm/AMD
        if self.optimization_profile.hardware.has_amd_gpu:
            try:
                # Check for AMD OCL
                if os.path.exists(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "amdocl.dll")):
                    self.optimization_profile.hardware.has_rocm = True
                    logger.info("AMD OCL detected")
                # Check for HIP runtime
                if os.path.exists(os.path.join(os.environ.get("SystemDrive", "C:"), "Program Files", "AMD", "ROCm")):
                    self.optimization_profile.hardware.has_rocm = True
                    logger.info("ROCm installation detected")
            except Exception as e:
                logger.warning(f"Failed to check for ROCm/HIP: {e}")
    
    def _detect_gpu_linux(self) -> None:
        """Определяет GPU на Linux."""
        try:
            # Check for NVIDIA GPUs using nvidia-smi
            nvidia_cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]
            nvidia_result = subprocess.run(nvidia_cmd, capture_output=True, text=True)
            
            if nvidia_result.returncode == 0:
                self.optimization_profile.hardware.has_nvidia_gpu = True
                lines = nvidia_result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(',')
                    if len(parts) >= 2:
                        self.optimization_profile.hardware.gpu_model = parts[0].strip()
                        # Parse memory (typically in MiB)
                        memory_str = parts[1].strip()
                        if "MiB" in memory_str:
                            try:
                                vram = float(memory_str.replace("MiB", "").strip())
                                self.optimization_profile.hardware.gpu_vram = int(vram * 1.049)  # Convert to MB
                            except:
                                pass
                
                self.optimization_profile.hardware.has_cuda = True
            else:
                # Check for AMD GPUs
                amd_cmd = ["lspci", "-v"]
                amd_result = subprocess.run(amd_cmd, capture_output=True, text=True)
                
                if amd_result.returncode == 0:
                    output = amd_result.stdout
                    if "AMD" in output or "Radeon" in output or "ATI" in output:
                        self.optimization_profile.hardware.has_amd_gpu = True
                        
                        # Try to extract the model name
                        import re
                        match = re.search(r"VGA.*?:\s*(AMD|ATI|Radeon).*?(\[.*?\])?", output)
                        if match:
                            self.optimization_profile.hardware.gpu_model = match.group(0).split(":", 1)[1].strip()
                        
                        # Check for ROCm
                        rocm_cmd = ["rocminfo"]
                        rocm_result = subprocess.run(rocm_cmd, capture_output=True, text=True)
                        if rocm_result.returncode == 0:
                            self.optimization_profile.hardware.has_rocm = True
        except Exception as e:
            logger.warning(f"Failed to detect GPU on Linux: {e}")
            raise
    
    def _detect_gpu_macos(self) -> None:
        """Определяет GPU на macOS."""
        try:
            cmd = ["system_profiler", "SPDisplaysDataType"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check for Metal support
                metal_cmd = ["system_profiler", "SPDisplaysDataType", "|", "grep", "Metal"]
                metal_result = subprocess.run(metal_cmd, capture_output=True, shell=True, text=True)
                
                if "Supported" in metal_result.stdout:
                    self.optimization_profile.compilation_flags.use_metal = True
                    logger.info("Metal support detected")
                
                # Try to extract GPU info
                import re
                
                # Extract GPU model
                model_match = re.search(r"Chipset Model: (.*?)$", output, re.MULTILINE)
                if model_match:
                    self.optimization_profile.hardware.gpu_model = model_match.group(1).strip()
                
                # Check if it's AMD or NVIDIA
                if "AMD" in self.optimization_profile.hardware.gpu_model or "Radeon" in self.optimization_profile.hardware.gpu_model:
                    self.optimization_profile.hardware.has_amd_gpu = True
                elif "NVIDIA" in self.optimization_profile.hardware.gpu_model or "GeForce" in self.optimization_profile.hardware.gpu_model:
                    self.optimization_profile.hardware.has_nvidia_gpu = True
                
                # Extract VRAM info
                vram_match = re.search(r"VRAM \(.*?\): (\d+)\s*([GM]B)", output, re.MULTILINE | re.IGNORECASE)
                if vram_match:
                    vram_amount = int(vram_match.group(1))
                    vram_unit = vram_match.group(2).upper()
                    
                    if vram_unit == "GB":
                        self.optimization_profile.hardware.gpu_vram = vram_amount * 1024
                    else:  # MB
                        self.optimization_profile.hardware.gpu_vram = vram_amount
        except Exception as e:
            logger.warning(f"Failed to detect GPU on macOS: {e}")
            raise
    
    def _fallback_gpu_detection(self) -> None:
        """Запасной метод для предположения о GPU на основе CPU."""
        cpu_model = self.optimization_profile.hardware.cpu_model.lower()
        
        # Intel integrated graphics fallback detection
        if "intel" in cpu_model:
            gen = 0
            if "13th" in cpu_model or "12th" in cpu_model:
                # Intel Iris Xe Graphics (Gen 12)
                gpu_model = "Intel Iris Xe Graphics"
                vram = 2048  # Usually shares with system RAM
                gen = 12
            elif "11th" in cpu_model or "10th" in cpu_model:
                # Intel UHD Graphics (Gen 11)
                gpu_model = "Intel UHD Graphics"
                vram = 1536
                gen = 11
            elif "9th" in cpu_model or "8th" in cpu_model or "7th" in cpu_model:
                # Intel UHD Graphics 630/620
                gpu_model = "Intel UHD Graphics 630"
                vram = 1024
                gen = 9
            else:
                # Older Intel HD Graphics
                gpu_model = "Intel HD Graphics"
                vram = 512
                gen = 7
            
            self.optimization_profile.hardware.gpu_model = gpu_model
            self.optimization_profile.hardware.gpu_vram = vram
            
            logger.info(f"Using fallback Intel GPU detection: {gpu_model} (Gen {gen}) with estimated {vram} MB VRAM")
        # AMD APU fallback detection
        elif "amd" in cpu_model and ("ryzen" in cpu_model or "apu" in cpu_model):
            if "7" in cpu_model or "6" in cpu_model:  # Newer Ryzen
                gpu_model = "AMD Radeon Graphics (integrated)"
                vram = 2048
            else:  # Older Ryzen
                gpu_model = "AMD Vega Graphics (integrated)"
                vram = 1024
            
            self.optimization_profile.hardware.gpu_model = gpu_model
            self.optimization_profile.hardware.gpu_vram = vram
            self.optimization_profile.hardware.has_amd_gpu = True
            
            logger.info(f"Using fallback AMD integrated GPU detection: {gpu_model} with estimated {vram} MB VRAM")
        # Desktop PC fallback - assume discrete GPU might exist
        else:
            logger.warning("Could not detect GPU, using conservative estimates")
            self.optimization_profile.hardware.gpu_model = "Unknown GPU"
            self.optimization_profile.hardware.gpu_vram = 0  # Conservative estimate
    
    def _save_profile(self) -> None:
        """Сохраняет профиль оптимизации в файл."""
        try:
            # Убедимся, что директория существует
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            
            # Конвертируем dataclass в JSON-совместимый словарь
            profile_dict = {
                "hardware": asdict(self.optimization_profile.hardware),
                "compilation_flags": asdict(self.optimization_profile.compilation_flags),
                "runtime_parameters": asdict(self.optimization_profile.runtime_parameters),
                "benchmark_results": [asdict(result) for result in self.optimization_profile.benchmark_results],
                "created_at": self.optimization_profile.created_at,
                "updated_at": self.optimization_profile.updated_at
            }
            
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile_dict, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Профиль оптимизации сохранен в {self.profile_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля: {e}")

    def optimize_compilation_flags(self) -> CompilationFlags:
        """Оптимизирует флаги компиляции llama.cpp под текущее оборудование."""
        flags = self.optimization_profile.compilation_flags
        hardware = self.optimization_profile.hardware
        
        # Базовые флаги CMake
        flags.cmake_flags = ["-DCMAKE_BUILD_TYPE=Release"]
        
        # Флаги в зависимости от процессора
        if flags.use_avx512:
            flags.cpu_arch_flags.extend(["-march=skylake-avx512", "-mavx512f", "-mavx512dq", "-mavx512bw", "-mavx512vl"])
        elif flags.use_avx2:
            flags.cpu_arch_flags.extend(["-march=haswell", "-mavx2", "-mfma"])
        elif flags.use_avx:
            flags.cpu_arch_flags.extend(["-march=sandybridge", "-mavx"])
        else:
            flags.cpu_arch_flags.append("-march=native")
        
        # CPU-специфичные оптимизации
        if "intel" in hardware.cpu_model.lower():
            flags.cmake_flags.append("-DLLAMA_BLAS=ON")
            flags.cmake_flags.append("-DLLAMA_BLAS_VENDOR=Intel10_64lp")
        elif "amd" in hardware.cpu_model.lower():
            flags.cmake_flags.append("-DLLAMA_BLAS=ON")
            flags.cmake_flags.append("-DLLAMA_BLAS_VENDOR=FLAME")
        
        # Флаги для GPU
        if hardware.has_nvidia_gpu and hardware.has_cuda:
            flags.cmake_flags.append("-DLLAMA_CUDA=ON")
            # Если VRAM меньше 6ГБ, включаем режим экономии памяти
            if hardware.gpu_vram < 6000:
                flags.cmake_flags.append("-DLLAMA_CUDA_DMMV_X=32")
                flags.cmake_flags.append("-DLLAMA_CUDA_MMV_Y=32")
        
        if hardware.has_amd_gpu and hardware.has_rocm:
            flags.cmake_flags.append("-DLLAMA_HIPBLAS=ON")
        
        if flags.use_vulkan:
            flags.cmake_flags.append("-DLLAMA_VULKAN=ON")
        
        if platform.system() == "Darwin":
            flags.cmake_flags.append("-DLLAMA_METAL=ON")
        
        # OpenMP для многопоточности
        if flags.use_openmp:
            flags.cmake_flags.append("-DLLAMA_NATIVE=ON")
        
        # Оптимизация компиляции
        flags.make_flags = [f"-j{hardware.cpu_threads}"]
        
        # Сохраняем обновленные флаги в профиле
        self.optimization_profile.compilation_flags = flags
        self._save_profile()
        
        return flags

    def optimize_runtime_parameters(self) -> RuntimeParameters:
        """Оптимизирует параметры запуска для модели."""
        params = self.optimization_profile.runtime_parameters
        hardware = self.optimization_profile.hardware
        
        # Оптимальное число потоков - обычно количество физических ядер или немного меньше
        optimal_threads = min(hardware.cpu_cores, max(1, hardware.cpu_cores - 1))
        params.n_threads = optimal_threads
        
        # Определение числа слоев для офлоада на GPU
        if hardware.has_nvidia_gpu and hardware.has_cuda:
            # Офлоад зависит от объема VRAM
            if hardware.gpu_vram >= 8000:  # 8+ ГБ VRAM
                params.n_gpu_layers = 32  # Большинство слоев
            elif hardware.gpu_vram >= 4000:  # 4-8 ГБ VRAM
                params.n_gpu_layers = 20  # Около половины слоев
            else:  # < 4 ГБ VRAM
                params.n_gpu_layers = 8  # Несколько слоев
        elif hardware.has_amd_gpu and hardware.has_rocm:
            # AMD GPUs обычно немного менее эффективны в этих задачах
            if hardware.gpu_vram >= 8000:
                params.n_gpu_layers = 28
            elif hardware.gpu_vram >= 4000:
                params.n_gpu_layers = 16
            else:
                params.n_gpu_layers = 4
        else:
            params.n_gpu_layers = 0
        
        # Оптимальный размер батча зависит от доступной памяти
        # Базовое эмпирическое правило: ~1MB на токен в батче для 7B модели
        if hardware.total_ram > 32000:  # >32 ГБ RAM
            params.batch_size = 1024
        elif hardware.total_ram > 16000:  # >16 ГБ RAM
            params.batch_size = 512
        elif hardware.total_ram > 8000:  # >8 ГБ RAM
            params.batch_size = 256
        else:
            params.batch_size = 128
        
        # Размер контекста зависит от доступной памяти
        # Для 7B модели: ~2MB памяти на 1K токенов контекста
        if hardware.total_ram > 32000:  # >32 ГБ RAM
            params.context_size = 8192
        elif hardware.total_ram > 16000:  # >16 ГБ RAM
            params.context_size = 4096
        elif hardware.total_ram > 8000:  # >8 ГБ RAM
            params.context_size = 2048
        else:
            params.context_size = 1024
        
        params.n_ctx = params.context_size
        
        # Оптимизация распределения тензоров между несколькими GPU
        # В этой простой версии мы не реализуем множественное распределение,
        # но можно добавить эту функциональность позже
        
        # Сохраняем параметры
        self.optimization_profile.runtime_parameters = params
        self._save_profile()
        
        return params
    
    def run_benchmark(self, model_path: str, prompt: str = None, iterations: int = 3) -> BenchmarkResult:
        """
        Запускает бенчмарк с текущими параметрами.
        
        Args:
            model_path: Путь к модели для тестирования
            prompt: Текст для генерации (если None, будет использован стандартный)
            iterations: Количество итераций для усреднения результатов
        
        Returns:
            BenchmarkResult: Результаты бенчмарка
        """
        if prompt is None:
            prompt = "Explain the theory of relativity in simple terms."
        
        params = self.optimization_profile.runtime_parameters
        
        # Проверяем, что у нас есть llama-server
        server_path = self._get_llama_server_path()
        if not server_path:
            logger.error("llama-server executable not found")
            return BenchmarkResult(prompt=prompt)
        
        # Запускаем сервер с текущими параметрами
        server_cmd = [
            server_path,
            "--model", model_path,
            "--threads", str(params.n_threads),
            "--ctx-size", str(params.context_size),
            "--batch-size", str(params.batch_size),
            "--n-gpu-layers", str(params.n_gpu_layers),
            "--embedding"
        ]
        
        # Запуск бенчмарка
        result = BenchmarkResult(prompt=prompt)
        result.config = {
            "threads": params.n_threads,
            "context_size": params.context_size,
            "batch_size": params.batch_size,
            "n_gpu_layers": params.n_gpu_layers,
        }
        
        try:
            # Запускаем сервер в фоновом режиме
            logger.info(f"Starting benchmark with command: {' '.join(server_cmd)}")
            server_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем немного, чтобы сервер запустился
            time.sleep(5)
            
            # Готовим запрос для бенчмарка
            import requests
            json_data = {
                "prompt": prompt,
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            tokens_per_second_list = []
            latency_list = []
            
            # Выполняем несколько итераций
            for i in range(iterations):
                start_time = time.time()
                try:
                    response = requests.post(
                        "http://localhost:8080/completion",
                        json=json_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        end_time = time.time()
                        data = response.json()
                        
                        # Вычисляем метрики
                        tokens_generated = len(data.get("content", "").split())
                        total_time = end_time - start_time
                        
                        tokens_per_second = tokens_generated / total_time
                        latency = total_time * 1000  # в миллисекундах
                        
                        tokens_per_second_list.append(tokens_per_second)
                        latency_list.append(latency)
                        
                        logger.info(f"Benchmark iteration {i+1}/{iterations}: " +
                                  f"{tokens_per_second:.2f} tokens/sec, {latency:.2f} ms latency")
                    else:
                        logger.error(f"Benchmark request failed with status {response.status_code}")
                except Exception as e:
                    logger.error(f"Benchmark request failed: {e}")
                
                time.sleep(2)  # Пауза между итерациями
            
            # Завершаем сервер
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except:
                server_process.kill()
            
            # Вычисляем средние значения
            if tokens_per_second_list:
                result.tokens_per_second = sum(tokens_per_second_list) / len(tokens_per_second_list)
            if latency_list:
                result.latency_ms = sum(latency_list) / len(latency_list)
            
            # Получаем использованную память
            result.memory_used_mb = self._measure_memory_usage()
            
            # Добавляем результат в профиль
            self.optimization_profile.benchmark_results.append(result)
            self._save_profile()
            
            return result
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            # В случае ошибки убиваем процесс сервера, если он еще жив
            try:
                server_process.terminate()
            except:
                pass
            
            return result

    def run_mock_benchmark(self, model_path: str, prompt: str = None, iterations: int = 1) -> BenchmarkResult:
        """
        Запускает имитацию бенчмарка без реального сервера для тестирования.
        
        Args:
            model_path: Путь к модели для тестирования
            prompt: Текст для генерации (если None, будет использован стандартный)
            iterations: Количество итераций для усреднения результатов
        
        Returns:
            BenchmarkResult: Имитация результатов бенчмарка
        """
        if prompt is None:
            prompt = "Объясни теорию относительности простыми словами."
        
        params = self.optimization_profile.runtime_parameters
        hardware = self.optimization_profile.hardware
        
        logger.info(f"Запуск имитации бенчмарка для модели: {model_path}")
        logger.info(f"Параметры: threads={params.n_threads}, n_ctx={params.n_ctx}, batch={params.batch_size}, gpu_layers={params.n_gpu_layers}")
        
        # Измеряем текущее использование памяти
        memory_used = self._measure_memory_usage()
        
        # Искусственно рассчитываем скорость генерации на основе характеристик оборудования
        # Это очень приблизительная формула, только для демонстрации
        base_speed = 15.0  # базовая скорость в токенах/сек
        
        # CPU влияние (более быстрый CPU = больше токенов/сек)
        cpu_factor = min(hardware.cpu_threads / 2, 2.0)
        
        # RAM влияние
        ram_factor = min(hardware.total_ram / 8000, 2.0)  # нормализуем по отношению к 8GB
        
        # Расчет влияния GPU (если используется)
        gpu_factor = 1.0
        if params.n_gpu_layers > 0 and hardware.gpu_vram > 0:
            gpu_factor = 1.5 + (min(hardware.gpu_vram / 4000, 2.0))  # VRAM в соотношении к 4GB
        
        # Размер батча
        batch_factor = min(params.batch_size / 256, 1.5)
        
        # Финальный расчет скорости
        tokens_per_second = base_speed * cpu_factor * ram_factor * gpu_factor * batch_factor
        
        # Расчет латентности
        latency_ms = 100 / cpu_factor  # базовая латентность 100ms, уменьшается с ростом CPU
        
        # Добавляем немного случайности для реалистичности
        import random
        tokens_per_second *= (0.9 + random.random() * 0.2)  # ±10%
        latency_ms *= (0.9 + random.random() * 0.2)  # ±10%
        
        # Создаем результат
        result = BenchmarkResult(
            tokens_per_second=tokens_per_second,
            latency_ms=latency_ms,
            memory_used_mb=memory_used,
            temperature_max=70.0,
            prompt=prompt,
            config={
                "threads": params.n_threads,
                "context_size": params.n_ctx,
                "batch_size": params.batch_size,
                "n_gpu_layers": params.n_gpu_layers,
            }
        )
        
        # Добавляем результат в профиль
        self.optimization_profile.benchmark_results.append(result)
        self._save_profile()
        
        logger.info(f"Имитация бенчмарка: {tokens_per_second:.2f} токенов/сек, латентность: {latency_ms:.2f} мс")
        return result
    
    def _get_llama_server_path(self) -> str:
        """Возвращает путь к llama-server."""
        # Ищем в наиболее вероятных местах
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                        "bin", "llama-server"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "bin", "llama-server.exe"),
            "/usr/local/bin/llama-server",
            "/usr/bin/llama-server",
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def _measure_memory_usage(self) -> int:
        """Измеряет текущее использование памяти."""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss // (1024 * 1024)  # Конвертируем в MB
        except:
            return 0
    
    def compile_optimized_server(self, llama_cpp_path: Optional[str] = None) -> bool:
        """
        Компилирует оптимизированную версию llama.cpp сервера.
        
        Args:
            llama_cpp_path: Путь к исходникам llama.cpp. Если None, попробуем скачать.
            
        Returns:
            bool: True если компиляция прошла успешно, иначе False
        """
        # Если путь не указан, скачиваем исходники
        if not llama_cpp_path:
            llama_cpp_path = self._download_llama_cpp()
            if not llama_cpp_path:
                logger.error("Failed to download llama.cpp sources")
                return False
        
        # Оптимизируем флаги компиляции
        flags = self.optimize_compilation_flags()
        
        # Создаем директорию для сборки
        build_dir = os.path.join(llama_cpp_path, "build")
        os.makedirs(build_dir, exist_ok=True)
        
        # Формируем команду для CMake
        cmake_cmd = ["cmake"] + flags.cmake_flags
        cmake_cmd.append("..")
        
        # Запускаем CMake
        logger.info(f"Running CMake with flags: {' '.join(cmake_cmd)}")
        try:
            subprocess.run(cmake_cmd, cwd=build_dir, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"CMake failed: {e}")
            return False
        
        # Запускаем сборку
        make_cmd = ["make"] + flags.make_flags + ["server"]
        logger.info(f"Building with command: {' '.join(make_cmd)}")
        try:
            subprocess.run(make_cmd, cwd=build_dir, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Build failed: {e}")
            return False
        
        # Копируем бинарник в папку bin проекта
        bin_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "bin")
        os.makedirs(bin_dir, exist_ok=True)
        
        server_bin = os.path.join(build_dir, "bin", "server")
        if platform.system() == "Windows":
            server_bin += ".exe"
        
        target_path = os.path.join(bin_dir, "llama-server")
        if platform.system() == "Windows":
            target_path += ".exe"
        
        try:
            shutil.copy2(server_bin, target_path)
            os.chmod(target_path, 0o755)  # Make executable
            logger.info(f"Compiled server copied to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy compiled server: {e}")
            return False
    
    def _download_llama_cpp(self) -> Optional[str]:
        """
        Скачивает исходники llama.cpp из репозитория.
        
        Returns:
            str: Путь к скачанным исходникам или None в случае ошибки
        """
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Downloading llama.cpp to {temp_dir}")
        
        try:
            # Клонируем репозиторий
            cmd = ["git", "clone", "https://github.com/ggerganov/llama.cpp.git", temp_dir]
            subprocess.run(cmd, check=True)
            return temp_dir
        except Exception as e:
            logger.error(f"Failed to download llama.cpp: {e}")
            return None
    
    def get_optimal_launch_parameters(self) -> Dict[str, Any]:
        """
        Возвращает оптимальные параметры запуска сервера.
        
        Returns:
            Dict[str, Any]: Словарь с параметрами запуска
        """
        params = self.optimization_profile.runtime_parameters
        
        return {
            "threads": params.n_threads,
            "ctx_size": params.context_size,
            "batch_size": params.batch_size,
            "n_gpu_layers": params.n_gpu_layers,
            "tensor_split": params.tensor_split,
            "n_ctx": params.n_ctx,
            "rope_freq_base": params.rope_freq_base,
            "rope_freq_scale": params.rope_freq_scale,
        }
    
    def run_optimization(self, model_path: str) -> Dict[str, Any]:
        """
        Запускает полную оптимизацию: обнаружение оборудования, компиляцию и бенчмаркинг.
        
        Args:
            model_path: Путь к модели для тестирования
            
        Returns:
            Dict[str, Any]: Результаты оптимизации
        """
        # 1. Обновляем профиль оборудования
        self._update_hardware_profile()
        
        # 2. Оптимизируем флаги компиляции
        compilation_flags = self.optimize_compilation_flags()
        
        # 3. Оптимизируем параметры запуска
        runtime_params = self.optimize_runtime_parameters()
        
        # 4. Запускаем бенчмарк
        benchmark_result = self.run_benchmark(model_path)
        
        # 5. Возвращаем результаты
        return {
            "hardware_profile": asdict(self.optimization_profile.hardware),
            "compilation_flags": asdict(compilation_flags),
            "runtime_parameters": asdict(runtime_params),
            "benchmark_result": asdict(benchmark_result) if benchmark_result else None,
        }


def main():
    """Точка входа для автономного запуска оптимизатора."""
    import argparse
    parser = argparse.ArgumentParser(description="Hardware Optimizer for GC-Forged-Pylot")
    parser.add_argument("--model", type=str, help="Path to the model file")
    parser.add_argument("--compile", action="store_true", help="Compile optimized server")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    parser.add_argument("--optimize", action="store_true", help="Run full optimization")
    parser.add_argument("--llama-cpp", type=str, help="Path to llama.cpp sources")
    
    args = parser.parse_args()
    
    optimizer = HardwareOptimizer()
    
    if args.optimize:
        if not args.model:
            print("Error: Model path is required for optimization")
            return
        results = optimizer.run_optimization(args.model)
        print("Optimization completed:")
        print(f"Hardware: {results['hardware_profile']}")
        print(f"Runtime parameters: {results['runtime_parameters']}")
        if results['benchmark_result']:
            print(f"Benchmark: {results['benchmark_result']['tokens_per_second']:.2f} tokens/sec")
    
    elif args.compile:
        success = optimizer.compile_optimized_server(args.llama_cpp)
        if success:
            print("Server compiled successfully")
        else:
            print("Server compilation failed")
    
    elif args.benchmark:
        if not args.model:
            print("Error: Model path is required for benchmarking")
            return
        result = optimizer.run_benchmark(args.model)
        print(f"Benchmark result: {result.tokens_per_second:.2f} tokens/sec, {result.latency_ms:.2f} ms latency")
    
    else:
        # По умолчанию просто обновляем профиль оборудования
        optimizer._update_hardware_profile()
        print("Hardware profile updated and saved")


if __name__ == "__main__":
    main()