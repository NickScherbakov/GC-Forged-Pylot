#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Адаптер для внешних LLM API
============================================

Модуль для интеграции внешних API языковых моделей (например, Ollama)
с основным кодом проекта.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
import time

# Добавляем родительский каталог в sys.path для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridge.proxy import ExternalLLMProxy
from .llm_interface import LLMInterface, LLMResponse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ExternalLLM")


class ExternalLLMAdapter(LLMInterface):
    """
    Адаптер для внешнего API LLM, соответствующий интерфейсу LLMInterface.
    
    Этот класс обеспечивает единый интерфейс для работы с внешними API
    языковых моделей, таких как Ollama или другие совместимые с OpenAI API.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует адаптер для внешнего API.
        
        Args:
            config: Конфигурация адаптера
        """
        super().__init__(config or {})
        
        api_config = self.config.get("external_api", {})
        api_url = api_config.get("url", "http://192.168.2.74:3131/v1")
        api_key = api_config.get("api_key", None)
        timeout = api_config.get("timeout", 60)
        
        self.default_model = self.config.get("default_model", "gpt-3.5-turbo")
        self.proxy = ExternalLLMProxy(api_url=api_url, api_key=api_key, timeout=timeout)
        self.connected = False
        
        # Проверяем соединение
        self._check_connection()
        
        logger.info(f"Адаптер ExternalLLM инициализирован с API {api_url}")
    
    def _check_connection(self) -> bool:
        """
        Проверяет соединение с внешним API.
        
        Returns:
            bool: True, если соединение установлено, иначе False
        """
        try:
            self.connected = self.proxy.health_check()
            if self.connected:
                logger.info("Соединение с внешним API установлено")
            else:
                logger.warning("Не удалось установить соединение с внешним API")
            return self.connected
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {str(e)}")
            self.connected = False
            return False
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации.
            **kwargs: Дополнительные параметры генерации.
            
        Returns:
            LLMResponse: Объект с ответом и метаданными.
        """
        if not self.connected and not self._check_connection():
            return LLMResponse(
                text="Ошибка: нет соединения с API",
                metadata={"error": "connection_error"}
            )
        
        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", 256)
        temperature = kwargs.get("temperature", 0.7)
        top_p = kwargs.get("top_p", 0.95)
        stop = kwargs.get("stop", None)
        
        start_time = time.time()
        
        try:
            # Выполняем запрос к API
            result = self.proxy.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop
            )
            
            # Проверка на ошибки
            if "error" in result:
                return LLMResponse(
                    text=f"Произошла ошибка при обработке запроса: {result['error']}",
                    metadata={
                        "error": result["error"],
                        "elapsed_time": time.time() - start_time
                    }
                )
            
            # Извлекаем текст из ответа
            text = result.get("choices", [{}])[0].get("text", "")
            
            # Создаем ответ
            response = LLMResponse(
                text=text,
                metadata={
                    "model": model,
                    "elapsed_time": time.time() - start_time,
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p
                    }
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при генерации: {str(e)}")
            return LLMResponse(
                text=f"Произошла ошибка при обработке запроса: {str(e)}",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе истории сообщений.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}].
            **kwargs: Дополнительные параметры генерации.
            
        Returns:
            LLMResponse: Объект с ответом и метаданными.
        """
        if not self.connected and not self._check_connection():
            return LLMResponse(
                text="Ошибка: нет соединения с API",
                metadata={"error": "connection_error"}
            )
        
        model = kwargs.get("model", self.default_model)
        max_tokens = kwargs.get("max_tokens", 256)
        temperature = kwargs.get("temperature", 0.7)
        
        start_time = time.time()
        
        try:
            # Выполняем запрос к API
            result = self.proxy.generate_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Проверка на ошибки
            if "error" in result:
                return LLMResponse(
                    text=f"Произошла ошибка при обработке запроса: {result['error']}",
                    metadata={
                        "error": result["error"],
                        "elapsed_time": time.time() - start_time
                    }
                )
            
            # Извлекаем текст из ответа
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Создаем ответ
            response = LLMResponse(
                text=text,
                metadata={
                    "model": model,
                    "elapsed_time": time.time() - start_time,
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка при генерации чата: {str(e)}")
            return LLMResponse(
                text=f"Произошла ошибка при обработке запроса: {str(e)}",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга.
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов.
        """
        if not self.connected and not self._check_connection():
            logger.error("Нет соединения с API для получения эмбеддингов")
            return [[0.0] * 768] * len(texts)  # Возвращаем нулевые векторы
        
        try:
            embedding_model = self.config.get("external_api", {}).get("embedding_model", "text-embedding-ada-002")
            result = self.proxy.generate_embeddings(texts=texts, model=embedding_model)
            
            if "error" in result:
                logger.error(f"Ошибка при получении эмбеддингов: {result['error']}")
                return [[0.0] * 768] * len(texts)
            
            # Извлекаем векторы из ответа
            embeddings = []
            for item in result.get("data", []):
                embeddings.append(item.get("embedding", [0.0] * 768))
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Ошибка при получении эмбеддингов: {str(e)}")
            return [[0.0] * 768] * len(texts)  # Возвращаем нулевые векторы
    
    def tokenize(self, text: str) -> List[int]:
        """
        Токенизирует текст. При внешнем API точная токенизация недоступна.
        
        Args:
            text: Текст для токенизации.
            
        Returns:
            List[int]: Приблизительный список токенов (заглушка).
        """
        # Для внешнего API точная токенизация обычно недоступна
        # Возвращаем приблизительную оценку токенов (1 токен ≈ 4 символа)
        return list(range(len(text) // 4 + 1))
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Детокенизирует список токенов. Для внешнего API не реализовано.
        
        Args:
            tokens: Список токенов.
            
        Returns:
            str: Пустая строка (заглушка).
        """
        logger.warning("Детокенизация не поддерживается для внешнего API")
        return ""
    
    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте.
        
        Args:
            text: Текст для подсчета токенов.
            
        Returns:
            int: Приблизительное количество токенов.
        """
        # Приблизительная оценка (1 токен ≈ 4 символа)
        return len(text) // 4 + 1
    
    def get_max_context_length(self) -> int:
        """
        Возвращает максимальную длину контекста для модели.
        
        Returns:
            int: Максимальная длина контекста.
        """
        # Возвращаем стандартное значение для большинства моделей
        return self.config.get("external_api", {}).get("max_context_length", 4096)
    
    def shutdown(self) -> None:
        """Очищает ресурсы."""
        self.connected = False
        logger.info("Адаптер ExternalLLM выключен")


# Пример конфигурации
EXAMPLE_CONFIG = {
    "external_api": {
        "url": "http://192.168.2.74:3131/v1",
        "api_key": "",  # Если требуется
        "timeout": 60,
        "embedding_model": "text-embedding-ada-002",
        "max_context_length": 4096
    },
    "default_model": "gpt-3.5-turbo"
}


if __name__ == "__main__":
    # Пример использования
    llm = ExternalLLMAdapter(EXAMPLE_CONFIG)
    
    if llm.connected:
        response = llm.generate("Расскажи короткую историю о программисте.")
        print(f"Ответ: {response.text}")
        print(f"Метаданные: {response.metadata}")
    else:
        print("Не удалось подключиться к API.")