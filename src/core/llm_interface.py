#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Интерфейс для языковых моделей
===============================================

Базовый интерфейс для взаимодействия с языковыми моделями.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Результат выполнения запроса к языковой модели."""
    text: str
    metadata: Dict[str, Any] = None


class LLMInterface:
    """
    Базовый интерфейс для языковых моделей.
    
    Этот класс определяет общий интерфейс для всех языковых моделей,
    используемых в системе GC-Forged Pylot.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует интерфейс LLM.
        
        Args:
            config: Конфигурация для LLM
        """
        self.config = config or {}
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации
            **kwargs: Дополнительные параметры генерации
            
        Returns:
            LLMResponse: Объект с ответом и метаданными
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе истории сообщений.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}]
            **kwargs: Дополнительные параметры генерации
            
        Returns:
            LLMResponse: Объект с ответом и метаданными
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def tokenize(self, text: str) -> List[int]:
        """
        Токенизирует текст.
        
        Args:
            text: Текст для токенизации
            
        Returns:
            List[int]: Список идентификаторов токенов
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Преобразует токены обратно в текст.
        
        Args:
            tokens: Список идентификаторов токенов
            
        Returns:
            str: Декодированный текст
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте.
        
        Args:
            text: Текст для подсчета токенов
            
        Returns:
            int: Количество токенов
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")
    
    def get_max_context_length(self) -> int:
        """
        Возвращает максимальную длину контекста для модели.
        
        Returns:
            int: Максимальная длина контекста в токенах
        """
        raise NotImplementedError("Метод должен быть реализован в дочернем классе")