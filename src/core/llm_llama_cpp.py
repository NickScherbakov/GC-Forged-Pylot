#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Интеграция с llama.cpp
========================================

Модуль для локального запуска языковых моделей через библиотеку llama.cpp.
Предоставляет интерфейс для загрузки моделей, управления параметрами
и выполнения запросов к моделям.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import threading
import time

try:
    from llama_cpp import Llama, LlamaCache
    from llama_cpp.llama_chat_format import ChatFormatter, format_messages
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("llama-cpp-python не установлен. Установите командой: pip install llama-cpp-python")

from .llm_interface import LLMInterface, LLMResponse


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("LlamaCpp")


class ModelConfig:
    """Конфигурация модели llama.cpp."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Инициализирует конфигурацию модели.
        
        Args:
            config_dict: Словарь с параметрами конфигурации.
        """
        # Путь к файлу модели
        self.model_path = config_dict.get("model_path", "")
        
        # Основные параметры модели
        self.n_ctx = config_dict.get("n_ctx", 4096)  # Размер контекста
        self.n_batch = config_dict.get("n_batch", 512)  # Размер батча для вывода
        self.n_gpu_layers = config_dict.get("n_gpu_layers", 0)  # Количество слоев на GPU
        self.main_gpu = config_dict.get("main_gpu", 0)  # Основная GPU
        self.tensor_split = config_dict.get("tensor_split", None)  # Распределение тензоров
        self.seed = config_dict.get("seed", -1)  # Сид для воспроизводимости
        
        # Оптимизации памяти
        self.use_mmap = config_dict.get("use_mmap", True)  # Использование memory mapping
        self.use_mlock = config_dict.get("use_mlock", False)  # Блокировка памяти
        self.rope_freq_base = config_dict.get("rope_freq_base", 0)  # RoPE frequency base
        self.rope_freq_scale = config_dict.get("rope_freq_scale", 0)  # RoPE frequency scale
        
        # Параметры для генерации текста
        self.max_tokens = config_dict.get("max_tokens", 2048)  # Максимальное количество токенов
        self.temperature = config_dict.get("temperature", 0.7)  # Температура
        self.top_p = config_dict.get("top_p", 0.9)  # Sampling top-p
        self.top_k = config_dict.get("top_k", 40)  # Sampling top-k
        self.repeat_penalty = config_dict.get("repeat_penalty", 1.1)  # Штраф за повторение
        self.presence_penalty = config_dict.get("presence_penalty", 0.0)  # Штраф за наличие
        self.frequency_penalty = config_dict.get("frequency_penalty", 0.0)  # Штраф за частоту
        
        # Кэширование
        self.cache_capacity = config_dict.get("cache_capacity", 2000)  # Объем кэша
        
        # Параметры формата чата
        self.chat_format = config_dict.get("chat_format", "llama-2")  # Формат сообщений чата
        self.system_prompt = config_dict.get("system_prompt", "")  # Системный промпт
        
        # Дополнительные опции
        self.verbose = config_dict.get("verbose", False)  # Подробный вывод
        self.embedding = config_dict.get("embedding", False)  # Режим эмбеддингов


class LLamaLLM(LLMInterface):
    """
    Реализация интерфейса LLM для работы с llama.cpp.
    
    Класс обеспечивает загрузку моделей через llama.cpp и выполнение
    запросов к моделям локально на CPU или GPU.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует интерфейс llama.cpp.
        
        Args:
            config: Конфигурация для интерфейса и моделей.
        """
        super().__init__(config or {})
        
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python не установлен. Локальные модели недоступны.")
            return
        
        # Инициализация состояния
        self.models = {}  # Загруженные модели
        self.active_model = None  # Активная модель
        self.active_model_name = None  # Имя активной модели
        self.lock = threading.RLock()  # Блокировка для потокобезопасности
        
        # Загрузка моделей из конфигурации
        self._load_models_from_config()
    
    def _load_models_from_config(self) -> None:
        """Загружает модели, указанные в конфигурации."""
        models_config = self.config.get("models", {})
        default_model = self.config.get("default_model", "")
        
        for model_name, model_config in models_config.items():
            logger.info(f"Загрузка модели '{model_name}'...")
            try:
                success = self.load_model(model_name, model_config)
                if success and model_name == default_model:
                    logger.info(f"Установка '{model_name}' как модели по умолчанию")
                    self.set_active_model(model_name)
            except Exception as e:
                logger.error(f"Ошибка при загрузке модели '{model_name}': {str(e)}")
    
    def load_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        """
        Загружает модель llama.cpp.
        
        Args:
            model_name: Имя модели для обращения.
            model_config: Конфигурация модели.
            
        Returns:
            bool: True, если модель успешно загружена.
            
        Raises:
            FileNotFoundError: Если файл модели не найден.
            RuntimeError: При ошибке загрузки модели.
        """
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python не установлен.")
            return False
        
        config = ModelConfig(model_config)
        
        # Проверка существования файла модели
        model_path = Path(config.model_path).expanduser().resolve()
        if not model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")
        
        logger.info(f"Загрузка модели из {model_path}")
        
        try:
            with self.lock:
                # Создание экземпляра модели llama.cpp
                llm = Llama(
                    model_path=str(model_path),
                    n_ctx=config.n_ctx,
                    n_batch=config.n_batch,
                    n_gpu_layers=config.n_gpu_layers,
                    main_gpu=config.main_gpu,
                    tensor_split=config.tensor_split,
                    seed=config.seed,
                    use_mmap=config.use_mmap,
                    use_mlock=config.use_mlock,
                    rope_freq_base=config.rope_freq_base,
                    rope_freq_scale=config.rope_freq_scale,
                    verbose=config.verbose,
                    embedding=config.embedding
                )
                
                # Создание кэша для модели
                if config.cache_capacity > 0:
                    llm.cache = LlamaCache(capacity_bytes=config.cache_capacity * 1024 * 1024)
                
                # Сохранение модели и конфигурации
                self.models[model_name] = {
                    "model": llm,
                    "config": config
                }
                
                logger.info(f"Модель '{model_name}' успешно загружена")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели: {str(e)}")
            raise RuntimeError(f"Не удалось загрузить модель: {str(e)}")
    
    def unload_model(self, model_name: str) -> bool:
        """
        Выгружает модель из памяти.
        
        Args:
            model_name: Имя модели для выгрузки.
            
        Returns:
            bool: True, если модель успешно выгружена.
        """
        with self.lock:
            if model_name not in self.models:
                logger.warning(f"Модель '{model_name}' не загружена")
                return False
            
            if self.active_model_name == model_name:
                self.active_model = None
                self.active_model_name = None
            
            # Очистка ресурсов модели
            self.models[model_name]["model"] = None
            del self.models[model_name]
            
            logger.info(f"Модель '{model_name}' выгружена")
            return True
    
    def set_active_model(self, model_name: str) -> bool:
        """
        Устанавливает активную модель.
        
        Args:
            model_name: Имя модели для активации.
            
        Returns:
            bool: True, если модель успешно активирована.
        """
        with self.lock:
            if model_name not in self.models:
                logger.warning(f"Модель '{model_name}' не загружена")
                return False
            
            self.active_model = self.models[model_name]["model"]
            self.active_model_name = model_name
            
            logger.info(f"Модель '{model_name}' установлена как активная")
            return True
    
    def get_available_models(self) -> List[str]:
        """
        Возвращает список имен загруженных моделей.
        
        Returns:
            List[str]: Список имен доступных моделей.
        """
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """
        Возвращает информацию о модели.
        
        Args:
            model_name: Имя модели или None для активной модели.
            
        Returns:
            Dict[str, Any]: Информация о модели.
        """
        name = model_name or self.active_model_name
        
        if not name or name not in self.models:
            return {}
        
        model_data = self.models[name]
        model = model_data["model"]
        config = model_data["config"]
        
        return {
            "name": name,
            "model_path": config.model_path,
            "n_ctx": config.n_ctx,
            "n_gpu_layers": config.n_gpu_layers,
            "embedding": config.embedding,
            "n_vocab": model.n_vocab() if model else None,
            "n_params": model.params.n_params if model else None,
            "is_active": name == self.active_model_name
        }
    
    def _format_chat_messages(self, model, messages: List[Dict[str, str]], config: ModelConfig) -> str:
        """
        Форматирует сообщения чата в соответствии с форматом модели.
        
        Args:
            model: Экземпляр модели Llama.
            messages: Список сообщений в формате [{role: "user", content: "текст"}].
            config: Конфигурация модели.
            
        Returns:
            str: Отформатированный промпт для модели.
        """
        # Добавляем системный промпт, если он указан
        if config.system_prompt and messages and messages[0]["role"] != "system":
            messages = [{"role": "system", "content": config.system_prompt}] + messages
        
        try:
            # Используем встроенный форматтер ChatFormatter
            chat_formatter = ChatFormatter.from_name(config.chat_format)
            prompt = format_messages(messages, chat_formatter)
            return prompt
        except Exception as e:
            logger.warning(f"Ошибка при форматировании чата: {str(e)}. Используем базовое форматирование.")
            
            # Базовое форматирование, если встроенное недоступно
            formatted = ""
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    formatted += f"<|system|>\n{content}\n"
                elif role == "user":
                    formatted += f"<|user|>\n{content}\n"
                elif role == "assistant":
                    formatted += f"<|assistant|>\n{content}\n"
                else:
                    formatted += f"<|{role}|>\n{content}\n"
            
            formatted += "<|assistant|>\n"
            return formatted
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Генерирует ответ на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации.
            **kwargs: Дополнительные параметры генерации.
            
        Returns:
            LLMResponse: Объект с ответом и метаданными.
            
        Raises:
            RuntimeError: Если нет активной модели.
        """
        if not self.active_model:
            raise RuntimeError("Нет активной модели для генерации")
        
        model_data = self.models[self.active_model_name]
        model = model_data["model"]
        config = model_data["config"]
        
        # Параметры генерации с учетом переданных аргументов
        max_tokens = kwargs.get("max_tokens", config.max_tokens)
        temperature = kwargs.get("temperature", config.temperature)
        top_p = kwargs.get("top_p", config.top_p)
        top_k = kwargs.get("top_k", config.top_k)
        repeat_penalty = kwargs.get("repeat_penalty", config.repeat_penalty)
        presence_penalty = kwargs.get("presence_penalty", config.presence_penalty)
        frequency_penalty = kwargs.get("frequency_penalty", config.frequency_penalty)
        
        start_time = time.time()
        
        try:
            # Генерация ответа
            response = model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                echo=False  # Не возвращать промпт в ответе
            )
            
            # Извлечение результата
            if isinstance(response, dict):
                text = response.get("choices", [{}])[0].get("text", "")
            elif isinstance(response, list) and len(response) > 0:
                text = response[0].get("text", "")
            else:
                logger.error(f"Неизвестный формат ответа: {type(response)}")
                text = str(response)
            
            # Расчет метаданных
            elapsed_time = time.time() - start_time
            
            # Формирование ответа
            llm_response = LLMResponse(
                text=text,
                metadata={
                    "model": self.active_model_name,
                    "elapsed_time": elapsed_time,
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "top_k": top_k
                    }
                }
            )
            
            return llm_response
            
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
            
        Raises:
            RuntimeError: Если нет активной модели.
        """
        if not self.active_model:
            raise RuntimeError("Нет активной модели для чата")
        
        model_data = self.models[self.active_model_name]
        model = model_data["model"]
        config = model_data["config"]
        
        # Форматирование сообщений в соответствии с выбранным форматом чата
        formatted_prompt = self._format_chat_messages(model, messages, config)
        
        # Генерация ответа с использованием форматированного промпта
        return self.generate(formatted_prompt, **kwargs)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Получает эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга.
            
        Returns:
            List[List[float]]: Список векторов эмбеддингов.
            
        Raises:
            RuntimeError: Если нет активной модели или модель не поддерживает эмбеддинги.
        """
        if not self.active_model:
            raise RuntimeError("Нет активной модели для получения эмбеддингов")
        
        model_data = self.models[self.active_model_name]
        model = model_data["model"]
        config = model_data["config"]
        
        if not config.embedding:
            raise RuntimeError("Текущая модель не поддерживает эмбеддинги")
        
        embeddings = []
        for text in texts:
            try:
                # Получение эмбеддинга для текста
                embedding = model.embed(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Ошибка при получении эмбеддинга: {str(e)}")
                # В случае ошибки добавляем пустой вектор
                embeddings.append([0.0] * 768)  # Стандартный размер для большинства моделей
        
        return embeddings
    
    def tokenize(self, text: str) -> List[int]:
        """
        Токенизирует текст с помощью текущей модели.
        
        Args:
            text: Текст для токенизации.
            
        Returns:
            List[int]: Список идентификаторов токенов.
            
        Raises:
            RuntimeError: Если нет активной модели.
        """
        if not self.active_model:
            raise RuntimeError("Нет активной модели для токенизации")
        
        model = self.models[self.active_model_name]["model"]
        return model.tokenize(text.encode("utf-8"))
    
    def detokenize(self, tokens: List[int]) -> str:
        """
        Преобразует токены обратно в текст.
        
        Args:
            tokens: Список идентификаторов токенов.
            
        Returns:
            str: Декодированный текст.
            
        Raises:
            RuntimeError: Если нет активной модели.
        """
        if not self.active_model:
            raise RuntimeError("Нет активной модели для детокенизации")
        
        model = self.models[self.active_model_name]["model"]
        result = b""
        for token in tokens:
            result += model.detokenize([token])
        
        return result.decode("utf-8", errors="replace")
    
    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте.
        
        Args:
            text: Текст для подсчета токенов.
            
        Returns:
            int: Количество токенов.
        """
        tokens = self.tokenize(text)
        return len(tokens)
    
    def get_max_context_length(self) -> int:
        """
        Возвращает максимальную длину контекста для активной модели.
        
        Returns:
            int: Максимальная длина контекста в токенах.
        """
        if not self.active_model:
            return 0
        
        config = self.models[self.active_model_name]["config"]
        return config.n_ctx
    
    def shutdown(self) -> None:
        """Освобождает ресурсы и выгружает все модели."""
        with self.lock:
            models = list(self.models.keys())
            for model_name in models:
                self.unload_model(model_name)
            
            self.active_model = None
            self.active_model_name = None
            
            logger.info("Все модели выгружены")


# Пример конфигурации для использования в JSON-файле
EXAMPLE_CONFIG = {
    "default_model": "llama-2-7b",
    "models": {
        "llama-2-7b": {
            "model_path": "models/llama-2-7b-chat.Q4_K_M.gguf",
            "n_ctx": 4096,
            "n_gpu_layers": 0,
            "n_batch": 512,
            "chat_format": "llama-2",
            "system_prompt": "You are a helpful, respectful and honest assistant.",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        "mistral-7b": {
            "model_path": "models/mistral-7b-instruct-v0.2.Q5_K_M.gguf",
            "n_ctx": 8192,
            "n_gpu_layers": 0,
            "n_batch": 512,
            "chat_format": "mistral",
            "temperature": 0.7,
            "max_tokens": 4096
        }
    }
}


if __name__ == "__main__":
    # Пример использования
    config = {
        "default_model": "test-model",
        "models": {
            "test-model": {
                "model_path": "путь/к/модели.gguf",
                "n_ctx": 4096,
                "n_gpu_layers": 0
            }
        }
    }
    
    print("Пример конфигурации для LLamaLLM:")
    print(json.dumps(EXAMPLE_CONFIG, indent=2))