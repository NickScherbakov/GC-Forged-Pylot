#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Adapter for External LLM APIs
============================================

Module for integrating external language model APIs (e.g., Ollama, llama.cpp)
with the main project code.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, Generator, AsyncGenerator
import threading

# Add parent directory в sys.path для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Изменяем импорт с более конкретным указанием пути
from ..bridge.proxy import ExternalLLMProxy
from .llm_interface import LLMInterface, LLMResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ExternalLLM")


class ExternalLLMAdapter(LLMInterface):
    """
    Адаптер для внешнего API LLM, соответствующий интерфейсу LLMInterface.
    
    Этот класс обеспечивает единый интерфейс для работы с внешними API
    language models, таких как Ollama, llama.cpp или другие совместимые с OpenAI API.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует адаптер для внешнего API.
        
        Args:
            config: Конфигурация адаптера с параметрами:
                - external_api.url: URL API сервера (например, "http://localhost:8000/v1")
                - external_api.api_key: Ключ API для авторизации (если требуется)
                - external_api.timeout: Таймаут запросов в секундах
                - external_api.verify_ssl: Проверять ли SSL сертификаты
                - external_api.retry_attempts: Количество повторных попыток при сбоях
                - external_api.retry_delay: Задержка между повторными попытками
                - external_api.embedding_model: Модель для генерации эмбеддингов
                - external_api.max_context_length: Максимальная длина контекста
                - default_model: Модель по умолчанию для текстовой генерации
        """
        super().__init__(config or {})
        
        api_config = self.config.get("external_api", {})
        api_url = api_config.get("url", "http://localhost:8000/v1")
        api_key = api_config.get("api_key", None)
        timeout = api_config.get("timeout", 60)
        retry_attempts = api_config.get("retry_attempts", 3)
        retry_delay = api_config.get("retry_delay", 0.5)
        verify_ssl = api_config.get("verify_ssl", True)
        
        self.default_model = self.config.get("default_model", "gpt-3.5-turbo")
        self.proxy = ExternalLLMProxy(
            api_url=api_url,
            api_key=api_key,
            timeout=timeout,
            connection_retries=retry_attempts,
            connection_retry_delay=retry_delay,
            verify_ssl=verify_ssl
        )
        self.connected = False
        self.lock = threading.RLock()
        self.embedding_model = api_config.get("embedding_model", "text-embedding-ada-002")
        self._cached_models = None
        self._models_last_update = 0
        
        # Check соединение
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
                # Кэшируем список моделей
                self._update_models_cache()
            else:
                logger.warning("Не удалось установить соединение с внешним API")
            return self.connected
        except Exception as e:
            logger.error(f"Ошибка при проверке соединения: {str(e)}")
            self.connected = False
            return False
    
    def _update_models_cache(self) -> None:
        """
        Обновляет кэш доступных моделей.
        """
        try:
            self._cached_models = self.proxy.get_models()
            self._models_last_update = time.time()
            logger.debug(f"Кэш моделей обновлен. Доступно {len(self._cached_models)} моделей.")
        except Exception as e:
            logger.warning(f"Не удалось обновить кэш моделей: {e}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Возвращает список доступных моделей.
        
        Returns:
            List[Dict[str, Any]]: Список доступных моделей
        """
        with self.lock:
            # Update кэш моделей, если он старше 5 минут или пуст
            if self._cached_models is None or time.time() - self._models_last_update > 300:
                self._update_models_cache()
            
            return self._cached_models or []
    
    def generate(self, prompt: str, **kwargs) -> Union[LLMResponse, Generator[LLMResponse, None, None]]:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации.
            **kwargs: Дополнительные параметры генерации:
                - model: Модель для генерации
                - max_tokens: Максимальное количество токенов
                - temperature: Температура сэмплирования (0.0-1.0)
                - top_p: Параметр nucleus sampling (0.0-1.0)
                - top_k: Параметр top-k sampling
                - repeat_penalty: Штраф за повторение
                - stream: Потоковая генерация (режим генератора)
                - stop: Список строк для остановки генерации
            
        Returns:
            LLMResponse: Объект с ответом и метаданными.
            или Generator[LLMResponse, None, None]: Генератор ответов при stream=True
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
        top_k = kwargs.get("top_k", 40)
        repeat_penalty = kwargs.get("repeat_penalty", 1.1)
        stream = kwargs.get("stream", False)
        stop = kwargs.get("stop", None)
        
        start_time = time.time()
        
        try:
            # Потоковая генерация
            if stream:
                return self._stream_generate(prompt, model, max_tokens, temperature, top_p, top_k, repeat_penalty, stop)
            
            # Обычная генерация
            result = self.proxy.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
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
            
            # Получаем информацию о причине завершения
            finish_reason = result.get("choices", [{}])[0].get("finish_reason", "unknown")
            
            # Получаем информацию об использовании токенов
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", self.count_tokens(prompt))
            completion_tokens = usage.get("completion_tokens", self.count_tokens(text))
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
            
            # Create ответ
            response = LLMResponse(
                text=text,
                metadata={
                    "model": model,
                    "elapsed_time": time.time() - start_time,
                    "finish_reason": finish_reason,
                    "tokens_used": total_tokens,
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k,
                        "repeat_penalty": repeat_penalty
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
    
    def _stream_generate(self, prompt: str, model: str, max_tokens: int, temperature: float, 
                        top_p: float, top_k: int, repeat_penalty: float, stop: List[str]) -> Generator[LLMResponse, None, None]:
        """
        Генератор для потоковой генерации ответов.
        
        Args:
            prompt: Текстовый промпт
            model: Название модели
            max_tokens: Максимальное количество токенов
            temperature: Температура сэмплирования
            top_p: Параметр nucleus sampling
            top_k: Параметр top-k sampling
            repeat_penalty: Штраф за повторение
            stop: Список стоп-строк
            
        Yields:
            LLMResponse: Последовательные фрагменты ответа
        """
        start_time = time.time()
        
        try:
            stream_generator = self.proxy.generate_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stream=True,
                stop=stop
            )
            
            for chunk in stream_generator:
                if "error" in chunk:
                    yield LLMResponse(
                        text=f"Ошибка в потоковой генерации: {chunk['error']}",
                        metadata={
                            "error": chunk["error"],
                            "elapsed_time": time.time() - start_time
                        }
                    )
                    return
                
                # Извлекаем текст и метаданные из чанка
                chunk_text = chunk.get("choices", [{}])[0].get("text", "")
                finish_reason = chunk.get("choices", [{}])[0].get("finish_reason", None)
                
                elapsed = time.time() - start_time
                
                # Create и возвращаем ответ для каждого фрагмента
                yield LLMResponse(
                    text=chunk_text,
                    metadata={
                        "model": model,
                        "elapsed_time": elapsed,
                        "chunk": True,
                        "finish_reason": finish_reason
                    }
                )
                
        except Exception as e:
            logger.error(f"Ошибка в потоковой генерации: {e}")
            yield LLMResponse(
                text=f"Ошибка при потоковой генерации: {str(e)}",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Union[LLMResponse, Generator[LLMResponse, None, None]]:
        """
        Генерирует ответ на основе истории сообщений.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}].
            **kwargs: Дополнительные параметры генерации:
                - model: Модель для генерации
                - max_tokens: Максимальное количество токенов
                - temperature: Температура сэмплирования (0.0-1.0)
                - top_p: Параметр nucleus sampling (0.0-1.0)
                - stream: Потоковая генерация (режим генератора)
                - stop: Список строк для остановки генерации
            
        Returns:
            LLMResponse: Объект с ответом и метаданными.
            или Generator[LLMResponse, None, None]: Генератор ответов при stream=True
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
        stream = kwargs.get("stream", False)
        stop = kwargs.get("stop", None)
        
        start_time = time.time()
        
        try:
            # Потоковая генерация
            if stream:
                return self._stream_chat(messages, model, max_tokens, temperature, top_p, stop)
            
            # Обычная генерация
            result = self.proxy.generate_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=False,
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
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Получаем информацию о причине завершения
            finish_reason = result.get("choices", [{}])[0].get("finish_reason", "unknown")
            
            # Получаем информацию об использовании токенов
            usage = result.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            
            # Create ответ
            response = LLMResponse(
                text=text,
                metadata={
                    "model": model,
                    "elapsed_time": time.time() - start_time,
                    "finish_reason": finish_reason,
                    "tokens_used": total_tokens,
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p
                    }
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка в методе chat: {str(e)}")
            return LLMResponse(
                text=f"Произошла ошибка при обработке запроса: {str(e)}",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def _stream_chat(self, messages: List[Dict[str, str]], model: str, max_tokens: int,
                    temperature: float, top_p: float, stop: List[str]) -> Generator[LLMResponse, None, None]:
        """
        Генератор для потоковой генерации ответов чата.
        
        Args:
            messages: Список сообщений
            model: Название модели
            max_tokens: Максимальное количество токенов
            temperature: Температура сэмплирования
            top_p: Параметр nucleus sampling
            stop: Список стоп-строк
            
        Yields:
            LLMResponse: Последовательные фрагменты ответа
        """
        start_time = time.time()
        
        try:
            stream_generator = self.proxy.generate_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True,
                stop=stop
            )
            
            for chunk in stream_generator:
                if "error" in chunk:
                    yield LLMResponse(
                        text=f"Ошибка в потоковой генерации чата: {chunk['error']}",
                        metadata={
                            "error": chunk["error"],
                            "elapsed_time": time.time() - start_time
                        }
                    )
                    return
                
                # Извлекаем текст и метаданные из чанка
                chunk_text = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                finish_reason = chunk.get("choices", [{}])[0].get("finish_reason", None)
                
                elapsed = time.time() - start_time
                
                # Create и возвращаем ответ для каждого фрагмента
                yield LLMResponse(
                    text=chunk_text,
                    metadata={
                        "model": model,
                        "elapsed_time": elapsed,
                        "chunk": True,
                        "finish_reason": finish_reason
                    }
                )
                
        except Exception as e:
            logger.error(f"Ошибка в потоковой генерации чата: {e}")
            yield LLMResponse(
                text=f"Ошибка при потоковой генерации чата: {str(e)}",
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
            result = self.proxy.generate_embeddings(texts=texts, model=self.embedding_model)
            
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
        try:
            if hasattr(self, "proxy") and self.proxy:
                self.proxy.close()
            self.connected = False
            logger.info("Адаптер ExternalLLM выключен")
        except Exception as e:
            logger.warning(f"Ошибка при выключении адаптера ExternalLLM: {e}")


# Пример configuration
EXAMPLE_CONFIG = {
    "external_api": {
        "url": "http://localhost:8000/v1",
        "api_key": "",  # Если требуется
        "timeout": 60,
        "retry_attempts": 3,
        "retry_delay": 0.5,
        "verify_ssl": True,
        "embedding_model": "text-embedding-ada-002",
        "max_context_length": 4096
    },
    "default_model": "gpt-3.5-turbo"
}


if __name__ == "__main__":
    # Пример use
    llm = ExternalLLMAdapter(EXAMPLE_CONFIG)
    
    if llm.connected:
        # Проверка обычной генерации
        print("Тест генерации:")
        response = llm.generate("Расскажи короткую историю о программисте.")
        print(f"Ответ: {response.text}")
        print(f"Метаданные: {response.metadata}")
        
        # Проверка потоковой генерации
        print("\nТест потоковой генерации:")
        try:
            for chunk in llm.generate("Опиши красоту природы в пяти предложениях.", stream=True):
                print(chunk.text, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"Ошибка при потоковой генерации: {e}")
            
        # Проверка чата
        print("\nТест чата:")
        chat_response = llm.chat([
            {"role": "system", "content": "Ты полезный ассистент."},
            {"role": "user", "content": "Привет! Как ты можешь мне помочь?"}
        ])
        print(f"Ответ: {chat_response.text}")
        
        # Получение эмбеддингов
        print("\nТест эмбеддингов:")
        embeddings = llm.get_embeddings(["Тестовый текст для эмбеддинга"])
        print(f"Длина вектора эмбеддинга: {len(embeddings[0])}")
    else:
        print("Не удалось подключиться к API.")