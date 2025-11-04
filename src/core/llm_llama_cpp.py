#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Interface for llama.cpp
======================================

Module for interacting with language models through llama.cpp.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Generator
import psutil

try:
    import llama_cpp
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

from .llm_interface import LLMInterface, LLMResponse

logger = logging.getLogger(__name__)


class LLamaLLM(LLMInterface):
    """
    Класс для взаимодействия с языковыми моделями через llama.cpp.
    
    Реализует интерфейс LLMInterface для работы с локальными моделями
    через Python-биндинги llama.cpp.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует интерфейс LLamaLLM.
        
        Args:
            config: Конфигурация для LLM
                - model_path: Путь к файлу модели (GGUF)
                - n_ctx: Размер контекста (по умолчанию 4096)
                - n_threads: Количество потоков (авто-определение, если не указано)
                - n_gpu_layers: Количество слоев для GPU (-1 для всех)
                - use_gpu: Использовать ли GPU (по умолчанию True)
                - gpu_device: Устройство GPU (по умолчанию 0)
                - seed: Seed для генерации (по умолчанию 42)
                - verbose: Подробный вывод отладки (по умолчанию False)
                - use_mlock: Использовать mlock для предотвращения свопирования (по умолчанию True)
                - use_mmap: Использовать mmap для загрузки модели (по умолчанию True)
                - rope_scaling_type: Тип масштабирования RoPE (по умолчанию None)
        """
        super().__init__(config or {})
        self.model = None
        self.model_path = self.config.get("model_path", "")
        self.lock = threading.RLock()
        
        if not LLAMA_CPP_AVAILABLE:
            logger.warning("LLamaLLM - llama-cpp-python не установлен. Работаем в режиме заглушек.")
            return
        
        # Загружаем модель если путь указан
        if self.model_path and os.path.exists(self.model_path):
            self._initialize_model()
        else:
            logger.warning(f"Путь к модели не найден: {self.model_path}")
    
    def _initialize_model(self) -> bool:
        """
        Инициализирует модель llama.cpp.
        
        Returns:
            bool: Успешно ли загрузилась модель
        """
        if not LLAMA_CPP_AVAILABLE:
            return False
            
        try:
            # Определяем оптимальное количество потоков, если не указано
            n_threads = self.config.get("n_threads")
            if not n_threads:
                n_threads = psutil.cpu_count(logical=False) or 4
                
            # Конфигурация для GPU
            n_gpu_layers = 0
            if self.config.get("use_gpu", True):
                n_gpu_layers = self.config.get("n_gpu_layers", -1)
                # Устанавливаем переменные среды для GPU
                if self.config.get("gpu_backend") == "rocm":
                    os.environ["GGML_OPENCL_PLATFORM"] = "AMD"
                    os.environ["GGML_OPENCL_DEVICE"] = str(self.config.get("gpu_device", 0))
                    
            # Параметры для эффективного управления памятью
            use_mlock = self.config.get("use_mlock", True)
            use_mmap = self.config.get("use_mmap", True)
            
            # Оптимизация RoPE для длинных последовательностей, если указано
            rope_scaling = None
            if self.config.get("rope_scaling_type"):
                rope_scaling = {"type": self.config.get("rope_scaling_type"),
                               "factor": self.config.get("rope_scaling_factor", 1.0)}
            
            # Загрузка модели
            self.model = llama_cpp.Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("n_ctx", 4096),
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                seed=self.config.get("seed", 42),
                verbose=self.config.get("verbose", False),
                use_mlock=use_mlock,
                use_mmap=use_mmap,
                rope_scaling=rope_scaling
            )
            
            logger.info(f"Модель {os.path.basename(self.model_path)} успешно загружена")
            logger.info(f"Конфигурация: потоки={n_threads}, gpu_layers={n_gpu_layers}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации модели llama.cpp: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации
            **kwargs: Дополнительные параметры генерации:
                - max_tokens: Максимальное количество токенов (по умолчанию 256)
                - temperature: Температура сэмплирования (по умолчанию 0.7)
                - top_p: Параметр nucleus sampling (по умолчанию 0.95)
                - top_k: Параметр top-k sampling (по умолчанию 40)
                - repeat_penalty: Штраф за повторение (по умолчанию 1.1)
                - stream: Потоковая генерация (по умолчанию False)
                - stop: Список строк для остановки генерации
            
        Returns:
            LLMResponse: Объект с ответом и метаданными
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.generate вызван, но модель не загружена. Возвращаем заглушку.")
            return LLMResponse(
                text="[Эта функция недоступна, так как llama.cpp не установлен или модель не загружена]",
                metadata={"dummy": True, "elapsed_time": 0.0}
            )
            
        # Параметры генерации
        params = {
            "max_tokens": kwargs.get("max_tokens", 256),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
            "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
            "echo": kwargs.get("echo", False),
            "stream": kwargs.get("stream", False),
            "stop": kwargs.get("stop", [])
        }
            
        try:
            start_time = time.time()
            
            with self.lock:  # Блокируем доступ к модели для потоков
                # Потоковая генерация
                if params["stream"]:
                    return self._generate_stream(prompt, params)
                
                # Синхронная генерация
                completion = self.model.create_completion(
                    prompt=prompt,
                    **params
                )
                
            generated_text = completion["choices"][0]["text"]
            elapsed_time = time.time() - start_time
            
            # Собираем метаданные
            tokens_used = 0
            if "usage" in completion:
                tokens_used = completion["usage"].get("total_tokens", 0)
            else:
                # Примерная оценка использованных токенов
                tokens_used = self.count_tokens(prompt) + self.count_tokens(generated_text)
            
            return LLMResponse(
                text=generated_text,
                metadata={
                    "model": os.path.basename(self.model_path),
                    "elapsed_time": elapsed_time,
                    "tokens_used": tokens_used,
                    "finish_reason": completion["choices"][0].get("finish_reason", None)
                }
            )
            
        except Exception as e:
            logger.error(f"Ошибка при генерации текста: {e}")
            return LLMResponse(
                text=f"[Ошибка генерации: {str(e)}]",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def _generate_stream(self, prompt: str, params: Dict[str, Any]) -> Generator[LLMResponse, None, None]:
        """
        Реализация потоковой генерации текста.
        
        Args:
            prompt: Текстовый промпт
            params: Параметры генерации
            
        Yields:
            LLMResponse: Последовательные объекты с частями ответа
        """
        # Включаем потоковую генерацию
        params["stream"] = True
        start_time = time.time()
        
        try:
            for chunk in self.model.create_completion(prompt=prompt, **params):
                chunk_text = chunk["choices"][0]["text"]
                elapsed_time = time.time() - start_time
                
                yield LLMResponse(
                    text=chunk_text,
                    metadata={
                        "model": os.path.basename(self.model_path),
                        "elapsed_time": elapsed_time,
                        "chunk": True,
                        "finish_reason": chunk["choices"][0].get("finish_reason", None)
                    }
                )
                
        except Exception as e:
            logger.error(f"Ошибка при потоковой генерации текста: {e}")
            yield LLMResponse(
                text=f"[Ошибка генерации: {str(e)}]",
                metadata={"error": str(e), "elapsed_time": time.time() - start_time}
            )
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе истории сообщений.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}]
            **kwargs: Дополнительные параметры генерации (см. метод generate)
            
        Returns:
            LLMResponse: Объект с ответом и метаданными
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.chat вызван, но модель не загружена. Возвращаем заглушку.")
            return LLMResponse(
                text="[Эта функция недоступна, так как llama.cpp не установлен или модель не загружена]",
                metadata={"dummy": True, "elapsed_time": 0.0}
            )
            
        try:
            # Преобразуем сообщения в формат, понятный llama.cpp
            prompt = self._messages_to_prompt(messages)
            
            return self.generate(prompt, **kwargs)
            
        except Exception as e:
            logger.error(f"Ошибка в методе chat: {e}")
            return LLMResponse(
                text=f"[Ошибка в методе chat: {str(e)}]",
                metadata={"error": str(e)}
            )
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Преобразует список сообщений в формат промпта.
        
        Args:
            messages: Список сообщений
            
        Returns:
            str: Промпт для модели
        """
        result = []
        
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            if role == "system":
                result.append(f"<|system|>\n{content}\n")
            elif role == "user":
                result.append(f"<|user|>\n{content}\n")
            elif role == "assistant":
                result.append(f"<|assistant|>\n{content}\n")
            else:
                result.append(f"<|{role}|>\n{content}\n")
        
        # Добавляем маркер для ответа ассистента
        result.append("<|assistant|>\n")
        
        return "".join(result)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.get_embeddings вызван, но модель не загружена. Возвращаем заглушку.")
            return [[0.0] * 768] * len(texts)
            
        try:
            embeddings = []
            
            with self.lock:  # Защищаем доступ к модели
                for text in texts:
                    embedding = self.model.embed(text)
                    embeddings.append(embedding)
                    
            return embeddings
            
        except Exception as e:
            logger.error(f"Ошибка при получении эмбеддингов: {e}")
            return [[0.0] * 768] * len(texts)
    
    def tokenize(self, text: str) -> List[int]:
        """
        Токенизирует текст.
        
        Args:
            text: Текст для токенизации
            
        Returns:
            List[int]: Список идентификаторов токенов
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.tokenize вызван, но модель не загружена. Возвращаем заглушку.")
            return list(range(len(text) // 4 + 1))
            
        try:
            tokens = self.model.tokenize(text.encode('utf-8'))
            return tokens
            
        except Exception as e:
            logger.error(f"Ошибка при токенизации: {e}")
            return []
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Преобразует токены обратно в текст.
        
        Args:
            tokens: Список идентификаторов токенов
            
        Returns:
            str: Декодированный текст
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.detokenize вызван, но модель не загружена. Возвращаем заглушку.")
            return ""
            
        try:
            text = self.model.detokenize(tokens).decode('utf-8')
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при детокенизации: {e}")
            return ""
    
    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте.
        
        Args:
            text: Текст для подсчета токенов
            
        Returns:
            int: Количество токенов
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.count_tokens вызван, но модель не загружена. Возвращаем заглушку.")
            return len(text) // 4 + 1
            
        try:
            tokens = self.tokenize(text)
            return len(tokens)
            
        except Exception as e:
            logger.error(f"Ошибка при подсчете токенов: {e}")
            return 0
    
    def get_max_context_length(self) -> int:
        """
        Возвращает максимальную длину контекста для модели.
        
        Returns:
            int: Максимальная длина контекста в токенах
        """
        if not LLAMA_CPP_AVAILABLE or not self.model:
            logger.warning("LLamaLLM.get_max_context_length вызван, но модель не загружена. Возвращаем заглушку.")
            return 4096
            
        try:
            return self.model.n_ctx()
            
        except Exception as e:
            logger.error(f"Ошибка при получении максимальной длины контекста: {e}")
            return 4096
    
    def shutdown(self) -> None:
        """Освобождает ресурсы модели."""
        logger.info("LLamaLLM.shutdown вызван")
        self.model = None