#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Tool Manager
====================================

Module for managing tools available to the agent.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import json
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - PyYAML optional
    yaml = None

logger = logging.getLogger(__name__)


class Tool:
    """Базовый класс для инструмента."""
    
    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """
        Инициализирует инструмент.
        
        Args:
            name: Имя инструмента
            description: Описание инструмента
            config: Конфигурация инструмента
        """
        self.name = name
        self.description = description
        self.config = config or {}
    
    def execute(self, **kwargs) -> Any:
        """
        Выполняет инструмент с переданными аргументами.
        
        Args:
            **kwargs: Аргументы для выполнения
            
        Returns:
            Any: Результат выполнения инструмента
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")


class DummyTool(Tool):
    """Заглушка для инструмента, который не может быть загружен."""
    
    def __init__(self, name: str, description: str, error_message: str = ""):
        """
        Инициализирует заглушку инструмента.
        
        Args:
            name: Имя инструмента
            description: Описание инструмента
            error_message: Сообщение об ошибке
        """
        super().__init__(name, description)
        self.error_message = error_message
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Возвращает сообщение об ошибке вместо результата.
        
        Args:
            **kwargs: Аргументы для выполнения
            
        Returns:
            Dict[str, Any]: Сообщение об ошибке
        """
        logger.warning(f"Попытка выполнения заглушки инструмента '{self.name}'")
        return {
            "success": False,
            "error": self.error_message or f"Инструмент '{self.name}' недоступен",
            "input": kwargs
        }


class ToolManager:
    """
    Класс для управления инструментами, доступными агенту.
    
    Загружает, регистрирует и предоставляет доступ к инструментам,
    необходимым для выполнения различных задач.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализирует менеджер инструментов.
        
        Args:
            config: Конфигурация менеджера инструментов
        """
        self.config = config or {}
        self.tools: Dict[str, Tool] = {}  # Словарь доступных инструментов
        self.tool_configs = self.config.get("available_tools", [])  # Конфигурации инструментов
        self.manifest_paths = self._resolve_manifest_paths(self.config.get("manifest_paths", []))
        
        logger.info("Менеджер инструментов инициализирован")
        self._load_manifests()

        for tool_cfg in self.tool_configs:
            self.register_tool(tool_cfg)
    
    def register_tool(self, tool_config: Dict[str, Any]) -> bool:
        """
        Регистрирует инструмент на основе его конфигурации.
        
        Args:
            tool_config: Конфигурация инструмента
            
        Returns:
            bool: True, если инструмент зарегистрирован успешно, иначе False
        """
        tool_name = tool_config.get("name", "")
        if not tool_name:
            logger.error("Не указано имя инструмента")
            return False
        
        tool_description = tool_config.get("description", "")
        tool_path = tool_config.get("path")
        module_path = tool_config.get("module")
        module_path = module_path or tool_path or ""
        
        if not module_path:
            logger.error(f"Не указан путь/модуль инструмента '{tool_name}'")
            return False
        
        try:
            # Загружаем модуль инструмента
            module_path = os.path.normpath(module_path)
            if module_path.endswith(".py"):
                module_path = module_path[:-3]  # Удаляем расширение .py
            
            # Преобразуем путь в импортируемый путь
            module_path = module_path.replace(os.path.sep, ".")
            if module_path.startswith("."):
                module_path = module_path[1:]
                
            # Пробуем импортировать модуль
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                # Если не удалось, пробуем относительный импорт
                try:
                    module_path = "tools." + os.path.basename(module_path)
                    module = importlib.import_module(module_path)
                except ImportError as e:
                    logger.error(f"Не удалось импортировать модуль инструмента '{tool_name}': {str(e)}")
                    # Создаем заглушку
                    self.tools[tool_name] = DummyTool(tool_name, tool_description, f"Импорт не удался: {str(e)}")
                    return False
            
            # Получаем класс инструмента
            tool_class_name = tool_config.get("class_name")
            if tool_class_name:
                if not hasattr(module, tool_class_name):
                    logger.error(f"Класс '{tool_class_name}' не найден в модуле '{module_path}'")
                    # Создаем заглушку
                    self.tools[tool_name] = DummyTool(tool_name, tool_description, f"Класс '{tool_class_name}' не найден")
                    return False
                tool_class = getattr(module, tool_class_name)
            else:
                # Если имя класса не указано, ищем класс Tool в модуле
                tool_classes = [cls for name, cls in module.__dict__.items() if isinstance(cls, type) and issubclass(cls, Tool) and cls != Tool]
                if not tool_classes:
                    logger.error(f"В модуле '{module_path}' не найден класс инструмента")
                    # Создаем заглушку
                    self.tools[tool_name] = DummyTool(tool_name, tool_description, "Класс инструмента не найден")
                    return False
                tool_class = tool_classes[0]
            
            # Создаем экземпляр инструмента
            tool = tool_class(tool_name, tool_description, tool_config.get("config", {}))
            
            # Регистрируем инструмент
            self.tools[tool_name] = tool
            logger.info(f"Инструмент '{tool_name}' успешно зарегистрирован")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при регистрации инструмента '{tool_name}': {str(e)}")
            # Создаем заглушку
            self.tools[tool_name] = DummyTool(tool_name, tool_description, str(e))
            return False

    def _resolve_manifest_paths(self, manifest_entries: Union[str, List[str]]) -> List[Path]:
        """Формирует список путей к manifest-файлам."""
        if not manifest_entries:
            manifest_entries = ["config/tool_manifest.json"]
        elif isinstance(manifest_entries, str):
            manifest_entries = [manifest_entries]

        resolved_paths: List[Path] = []
        base_dir = Path.cwd()

        root_dir = Path(__file__).resolve().parents[2]
        if str(root_dir) not in sys.path:  # pragma: no cover - environment setup
            sys.path.append(str(root_dir))

        for entry in manifest_entries:
            path = Path(entry)
            if not path.is_absolute():
                path = base_dir / path
            if path.exists():
                resolved_paths.append(path)
            else:
                logger.warning(f"Файл манифеста инструментов не найден: {path}")
        return resolved_paths

    def _load_manifests(self) -> None:
        """Загружает инструменты из указанных манифестов."""
        for manifest_path in self.manifest_paths:
            manifest_data = self._parse_manifest(manifest_path)
            if not manifest_data:
                continue

            tools = manifest_data.get("tools", [])
            if not tools:
                logger.info(f"Манифест {manifest_path} не содержит инструментов")
                continue

            for tool_entry in tools:
                merged_config = dict(tool_entry)
                merged_config.setdefault("config", {})
                self.register_tool(merged_config)

    def _parse_manifest(self, manifest_path: Path) -> Optional[Dict[str, Any]]:
        """Читает манифест инструментов (JSON/YAML)."""
        try:
            content = manifest_path.read_text(encoding="utf-8")
            suffix = manifest_path.suffix.lower()

            if suffix in {".yaml", ".yml"}:
                if not yaml:
                    logger.error(f"PyYAML не установлен, пропускаем манифест {manifest_path}")
                    return None
                data = yaml.safe_load(content)  # type: ignore
            else:
                data = json.loads(content)

            schema_version = data.get("schema_version")
            if schema_version not in {"1.0", None}:
                logger.warning(f"Неизвестная версия схемы манифеста {schema_version} в {manifest_path}")

            manifest_name = data.get("metadata", {}).get("name", manifest_path.stem)
            logger.info(f"Загружаем манифест инструментов '{manifest_name}' из {manifest_path}")
            return data
        except Exception as exc:
            logger.error(f"Не удалось прочитать манифест инструментов {manifest_path}: {exc}")
            return None
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Возвращает инструмент по его имени.
        
        Args:
            tool_name: Имя инструмента
            
        Returns:
            Optional[Tool]: Инструмент или None, если инструмент не найден
        """
        return self.tools.get(tool_name)
    
    def has_tool(self, tool_name: str) -> bool:
        """
        Проверяет наличие инструмента.
        
        Args:
            tool_name: Имя инструмента
            
        Returns:
            bool: True, если инструмент существует, иначе False
        """
        return tool_name in self.tools
    
    def list_available_tools(self) -> List[str]:
        """
        Возвращает список доступных инструментов.
        
        Returns:
            List[str]: Список имен доступных инструментов
        """
        return list(self.tools.keys())