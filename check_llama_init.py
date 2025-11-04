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
    Проверяет, является ли это первым запуском системы.
    
    Returns:
        bool: True если это первый запуск, иначе False
    """
    # Проверяем наличие файла профиля оборудования
    hardware_profile_path = os.path.join("config", "hardware_profile.json")
    if not os.path.exists(hardware_profile_path):
        return True
    
    # Проверяем наличие директории bin с скомпилированным сервером
    bin_dir = os.path.join("bin")
    server_path = os.path.join(bin_dir, "llama-server")
    if platform.system() == "Windows":
        server_path += ".exe"
    
    if not os.path.exists(server_path):
        return True
    
    return False


def check_hardware_changes(optimizer: HardwareOptimizer) -> bool:
    """
    Проверяет наличие изменений в оборудовании.
    
    Args:
        optimizer: Инициализированный оптимизатор
    
    Returns:
        bool: True если обнаружены изменения, иначе False
    """
    return optimizer._is_profile_outdated()


def perform_optimization(quiet: bool = False, force: bool = False) -> bool:
    """
    Выполняет оптимизацию системы при необходимости.
    
    Args:
        quiet: Подавлять вывод
        force: Принудительная оптимизация
    
    Returns:
        bool: True если оптимизация выполнена успешно, иначе False
    """
    try:
        optimizer = HardwareOptimizer()
        
        # Проверяем необходимость оптимизации
        is_first_run = check_first_run()
        has_hardware_changes = check_hardware_changes(optimizer)
        
        if is_first_run or has_hardware_changes or force:
            if not quiet:
                if is_first_run:
                    logger.info("Первый запуск системы. Выполняем начальную оптимизацию.")
                elif has_hardware_changes:
                    logger.info("Обнаружены изменения в оборудовании. Выполняем переоптимизацию.")
                else:
                    logger.info("Принудительная оптимизация.")
            
            # Загружаем конфигурацию
            config = load_config()
            
            # Обновляем профиль оборудования
            optimizer._update_hardware_profile()
            
            # Оптимизируем параметры запуска
            optimizer.optimize_compilation_flags()
            optimizer.optimize_runtime_parameters()
            
            # Если есть доступная модель, выполняем бенчмаркинг
            if os.path.exists(config.model_path):
                if not quiet:
                    logger.info(f"Запуск бенчмарка на модели: {config.model_path}")
                
                try:
                    optimizer.run_benchmark(config.model_path, iterations=1)
                except Exception as e:
                    if not quiet:
                        logger.warning(f"Не удалось выполнить бенчмаркинг: {e}")
            
            # Если сервер еще не скомпилирован, пытаемся его собрать
            bin_dir = os.path.join("bin")
            server_path = os.path.join(bin_dir, "llama-server")
            if platform.system() == "Windows":
                server_path += ".exe"
            
            if not os.path.exists(server_path):
                if not quiet:
                    logger.info("Сервер не найден. Пытаемся скомпилировать.")
                
                try:
                    # Компиляция сервера (может быть продолжительной!)
                    compile_success = optimizer.compile_optimized_server()
                    
                    if not quiet:
                        if compile_success:
                            logger.info("Сервер успешно скомпилирован.")
                        else:
                            logger.warning("Не удалось скомпилировать сервер.")
                except Exception as e:
                    if not quiet:
                        logger.warning(f"Ошибка компиляции сервера: {e}")
            
            return True
        else:
            if not quiet:
                logger.info("Система уже оптимизирована.")
            return True
            
    except Exception as e:
        if not quiet:
            logger.error(f"Ошибка при оптимизации системы: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Проверка и оптимизация системы для запуска llama.cpp"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true", 
        help="Подавлять вывод сообщений"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Принудительная оптимизация"
    )
    
    args = parser.parse_args()
    
    success = perform_optimization(args.quiet, args.force)
    
    return 0 if success else 1


if __name__ == "__main__":
    import platform
    sys.exit(main())