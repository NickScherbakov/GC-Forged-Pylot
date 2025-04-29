#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Система памяти
=============================

Модуль для хранения и извлечения контекстной информации.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class Memory:
    """
    Класс для работы с памятью агента.
    
    Обеспечивает хранение истории взаимодействия и извлечение
    релевантного контекста для обработки запросов.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует систему памяти.
        
        Args:
            config: Конфигурация системы памяти
        """
        self.config = config or {}
        self.history = []
        self.history_path = self.config.get("history_path", "data/conversation_history.json")
        self.history_size = self.config.get("history_size", 10)
        self.initialized = False
        
        logger.info("Система памяти инициализирована")
    
    def initialize(self) -> None:
        """Инициализирует систему памяти и загружает историю, если доступно."""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                    logger.info(f"Загружено {len(self.history)} записей из истории")
        except Exception as e:
            logger.error(f"Ошибка при загрузке истории: {str(e)}")
        
        self.initialized = True
    
    def add_interaction(self, user_input: str, assistant_output: str) -> None:
        """
        Добавляет взаимодействие в историю.
        
        Args:
            user_input: Запрос пользователя
            assistant_output: Ответ ассистента
        """
        from datetime import datetime
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "assistant_output": assistant_output
        }
        
        self.history.append(interaction)
        
        # Ограничиваем размер истории
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]
    
    def get_relevant_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Извлекает релевантный контекст для запроса.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            Список релевантных записей из истории
        """
        # В простой реализации возвращаем всю историю
        # В более сложной реализации здесь был бы поиск релевантного контекста
        return self.history
    
    def clear(self) -> None:
        """Очищает историю взаимодействия."""
        self.history = []
        logger.info("История очищена")
    
    def save(self) -> bool:
        """
        Сохраняет историю взаимодействия в файл.
        
        Returns:
            bool: True, если сохранение успешно, иначе False
        """
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.info(f"История сохранена в {self.history_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории: {str(e)}")
            return False