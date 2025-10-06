#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Plugin Interface
==================================

Базовый интерфейс и менеджер для плагинов.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Task:
    """Представление задачи"""
    
    def __init__(self, description: str, type: str = "general", metadata: Dict[str, Any] = None):
        self.description = description
        self.type = type
        self.metadata = metadata or {}
        self.result = None
        self.status = "pending"


class Tool:
    """Представление инструмента"""
    
    def __init__(self, name: str, description: str, function: callable):
        self.name = name
        self.description = description
        self.function = function
    
    def execute(self, *args, **kwargs):
        """Выполнить инструмент"""
        return self.function(*args, **kwargs)


class PluginInterface(ABC):
    """Базовый интерфейс для всех плагинов"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = ""
        self.version = "0.0.0"
        self.author = ""
        self.enabled = True
    
    @abstractmethod
    def on_load(self) -> None:
        """
        Вызывается при загрузке плагина.
        Используйте для инициализации ресурсов.
        """
        pass
    
    def on_unload(self) -> None:
        """
        Вызывается при выгрузке плагина.
        Используйте для очистки ресурсов.
        """
        pass
    
    def on_task_start(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        Хук перед началом выполнения задачи.
        
        Args:
            task: Задача, которая будет выполнена
        
        Returns:
            Optional[Dict]: Метаданные для модификации задачи или None
        """
        return None
    
    def on_task_complete(self, task: Task, result: Any) -> Optional[Any]:
        """
        Хук после завершения задачи.
        
        Args:
            task: Завершенная задача
            result: Результат выполнения задачи
        
        Returns:
            Optional[Any]: Модифицированный результат или None
        """
        return None
    
    def on_task_error(self, task: Task, error: Exception) -> Optional[str]:
        """
        Хук при ошибке выполнения задачи.
        
        Args:
            task: Задача с ошибкой
            error: Возникшая ошибка
        
        Returns:
            Optional[str]: Сообщение об обработке ошибки или None
        """
        return None
    
    def on_improvement_cycle(self, cycle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Хук во время цикла самосовершенствования.
        
        Args:
            cycle_data: Данные о цикле (итерация, метрики и т.д.)
        
        Returns:
            Optional[Dict]: Модифицированные данные цикла или None
        """
        return None
    
    def on_code_generation(self, prompt: str, generated_code: str) -> Optional[str]:
        """
        Хук после генерации кода.
        
        Args:
            prompt: Промпт для генерации
            generated_code: Сгенерированный код
        
        Returns:
            Optional[str]: Модифицированный код или None
        """
        return None
    
    def add_tools(self) -> List[Tool]:
        """
        Добавить новые инструменты в систему.
        
        Returns:
            List[Tool]: Список новых инструментов
        """
        return []
    
    def get_info(self) -> Dict[str, Any]:
        """
        Получить информацию о плагине.
        
        Returns:
            Dict: Информация о плагине
        """
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": getattr(self, "description", ""),
            "enabled": self.enabled
        }
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """
        Настроить плагин с новой конфигурацией.
        
        Args:
            config: Новая конфигурация
        
        Returns:
            bool: True, если настройка прошла успешно
        """
        self.config.update(config)
        return True


class PluginManager:
    """Менеджер плагинов"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.tools: Dict[str, Tool] = {}
    
    def register_plugin(self, plugin: PluginInterface) -> bool:
        """
        Зарегистрировать плагин.
        
        Args:
            plugin: Экземпляр плагина
        
        Returns:
            bool: True, если регистрация прошла успешно
        """
        if plugin.name in self.plugins:
            logger.warning(f"Плагин {plugin.name} уже зарегистрирован")
            return False
        
        try:
            plugin.on_load()
            self.plugins[plugin.name] = plugin
            
            # Зарегистрировать инструменты плагина
            for tool in plugin.add_tools():
                self.tools[tool.name] = tool
            
            logger.info(f"Плагин {plugin.name} v{plugin.version} успешно загружен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при загрузке плагина {plugin.name}: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Отменить регистрацию плагина.
        
        Args:
            plugin_name: Имя плагина
        
        Returns:
            bool: True, если отмена регистрации прошла успешно
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Плагин {plugin_name} не найден")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            plugin.on_unload()
            del self.plugins[plugin_name]
            
            # Удалить инструменты плагина
            tools_to_remove = [
                name for name, tool in self.tools.items()
                if hasattr(tool, 'plugin') and tool.plugin == plugin_name
            ]
            for tool_name in tools_to_remove:
                del self.tools[tool_name]
            
            logger.info(f"Плагин {plugin_name} успешно выгружен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при выгрузке плагина {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Получить плагин по имени"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """Получить список всех плагинов"""
        return [plugin.get_info() for plugin in self.plugins.values()]
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Вызвать хук во всех активных плагинах.
        
        Args:
            hook_name: Имя хука
            *args, **kwargs: Аргументы для хука
        
        Returns:
            List[Any]: Результаты от всех плагинов
        """
        results = []
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            if hasattr(plugin, hook_name):
                try:
                    result = getattr(plugin, hook_name)(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Ошибка в плагине {plugin.name} при вызове хука {hook_name}: {e}")
        
        return results
    
    def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        Выполнить инструмент плагина.
        
        Args:
            tool_name: Имя инструмента
            *args, **kwargs: Аргументы для инструмента
        
        Returns:
            Any: Результат выполнения инструмента
        """
        if tool_name not in self.tools:
            raise ValueError(f"Инструмент {tool_name} не найден")
        
        return self.tools[tool_name].execute(*args, **kwargs)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """Получить список всех инструментов"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
