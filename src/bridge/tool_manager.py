#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Менеджер инструментов
====================================

Модуль для управления инструментами, доступными агенту.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)


class Tool:
    """Базовый класс для инструмента."""
    
    def __init__(self, name: str, description: str, config: Dict[str, Any] = None):
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
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует менеджер инструментов.
        
        Args:
            config: Конфигурация менеджера инструментов
        """
        self.config = config or {}
        self.tools = {}  # Словарь доступных инструментов
        self.tool_configs = self.config.get("available_tools", [])  # Конфигурации инструментов
        
        logger.info("Менеджер инструментов инициализирован")
    
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
        tool_path = tool_config.get("path", "")
        
        if not tool_path:
            logger.error(f"Не указан путь к модулю инструмента '{tool_name}'")
            return False
        
        try:
            # Загружаем модуль инструмента
            module_path = os.path.normpath(tool_path)
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