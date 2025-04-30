#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Загрузчик конфигурации
========================================

Модуль для загрузки конфигурационных файлов в различных форматах.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ConfigLoader")

def load_config(config_path: Union[str, Path], default_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Загружает конфигурацию из JSON-файла.
    
    Args:
        config_path: Путь к конфигурационному файлу (абсолютный или относительный)
        default_config: Конфигурация по умолчанию, если файл не найден
        
    Returns:
        Dict[str, Any]: Загруженная конфигурация или конфигурация по умолчанию
    """
    if not config_path:
        logger.warning("Путь к конфигурационному файлу не указан, используем значения по умолчанию")
        return default_config or {}
    
    config_path = Path(config_path)
    
    # Проверяем существование файла
    if not config_path.exists():
        logger.warning(f"Конфигурационный файл не найден: {config_path}, используем значения по умолчанию")
        return default_config or {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"Конфигурация успешно загружена из {config_path}")
            
            # Объединяем с конфигурацией по умолчанию, если она предоставлена
            if default_config:
                merged_config = default_config.copy()
                merged_config.update(config)
                return merged_config
                
            return config
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка синтаксиса JSON в конфигурационном файле {config_path}: {e}")
        return default_config or {}
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурационного файла {config_path}: {e}")
        return default_config or {}

def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
    """
    Сохраняет конфигурацию в JSON-файл.
    
    Args:
        config: Конфигурация для сохранения
        config_path: Путь к файлу для сохранения
        
    Returns:
        bool: True, если сохранение успешно, иначе False
    """
    if not config_path:
        logger.error("Путь для сохранения конфигурации не указан")
        return False
    
    config_path = Path(config_path)
    
    # Создаем родительский каталог, если он не существует
    os.makedirs(config_path.parent, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"Конфигурация успешно сохранена в {config_path}")
            return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении конфигурации в {config_path}: {e}")
        return False

if __name__ == "__main__":
    # Пример использования
    default_config = {
        "server": {
            "host": "localhost",
            "port": 8080,
            "verbose": False
        },
        "model": {
            "path": "models/default-model.gguf",
            "n_ctx": 2048,
            "n_gpu_layers": 0
        },
        "cache": {
            "enabled": True,
            "size": 100,
            "ttl": 3600
        }
    }
    
    sample_config_path = "sample_config.json"
    
    # Сохраняем пример конфигурации
    save_config(default_config, sample_config_path)
    
    # Загружаем пример конфигурации
    loaded_config = load_config(sample_config_path)
    
    print("Загруженная конфигурация:")
    print(json.dumps(loaded_config, ensure_ascii=False, indent=2))