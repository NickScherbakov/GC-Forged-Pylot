#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Прокси для внешних API
========================================

Модуль для взаимодействия с внешними API языковых моделей.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import sys
import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union, Callable

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ExternalLLMProxy")


class ExternalLLMProxy:
    """
    Прокси для взаимодействия с внешними API языковых моделей.
    
    Позволяет подключаться к внешним API, таким как Ollama или другие
    совместимые с OpenAI API сервисы.
    """
    
    def __init__(self, api_url: str, api_key: str = None, timeout: int = 60):
        """
        Инициализирует прокси для внешнего API.
        
        Args:
            api_url: URL API, например "http://192.168.2.74:3131/v1"
            api_key: Ключ API для авторизации (если требуется)
            timeout: Таймаут для запросов в секундах
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
        logger.info(f"Инициализация прокси для внешнего API: {self.api_url}")
    
    def _make_request(self, endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
        """
        Выполняет запрос к внешнему API.
        
        Args:
            endpoint: Конечная точка API, например "/completions"
            method: HTTP метод (GET, POST и т.д.)
            data: Данные для отправки в теле запроса
            
        Returns:
            Ответ от API в формате словаря
            
        Raises:
            ConnectionError: При ошибке подключения к API
            TimeoutError: При превышении таймаута ожидания ответа
            Exception: При других ошибках
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            else:  # Default to POST
                response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            
            elapsed = time.time() - start_time
            logger.debug(f"Запрос к {url} выполнен за {elapsed:.2f}с")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Ошибка API ({response.status_code}): {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения с API: {str(e)}")
            raise ConnectionError(f"Не удалось подключиться к API по адресу {url}: {str(e)}")
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Таймаут запроса к API: {str(e)}")
            raise TimeoutError(f"Превышено время ожидания ответа от API: {str(e)}")
        
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при запросе к API: {str(e)}")
            raise
    
    def get_models(self) -> List[Dict]:
        """
        Получает список доступных моделей.
        
        Returns:
            Список моделей в формате [{id: "model-id", ...}, ...]
        """
        try:
            response = self._make_request("/models", method="GET")
            return response.get("data", [])
        except Exception as e:
            logger.error(f"Ошибка при получении списка моделей: {str(e)}")
            return []
    
    def generate_completion(self, 
                            prompt: str, 
                            model: str = "gpt-3.5-turbo-instruct", 
                            max_tokens: int = 256,
                            temperature: float = 0.7,
                            top_p: float = 0.95,
                            stop: List[str] = None) -> Dict:
        """
        Генерирует текстовое завершение на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации
            model: ID модели для использования
            max_tokens: Максимальное количество токенов для генерации
            temperature: Температура сэмплирования (0.0-1.0)
            top_p: Параметр nucleus sampling (0.0-1.0)
            stop: Список стоп-последовательностей
            
        Returns:
            Результат генерации в формате словаря
        """
        data = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        if stop:
            data["stop"] = stop
            
        try:
            return self._make_request("/completions", data=data)
        except Exception as e:
            logger.error(f"Ошибка при генерации завершения: {str(e)}")
            return {"error": str(e)}
    
    def generate_chat_completion(self, 
                                messages: List[Dict[str, str]], 
                                model: str = "gpt-3.5-turbo",
                                temperature: float = 0.7,
                                max_tokens: int = 256) -> Dict:
        """
        Генерирует ответ на основе истории сообщений в формате чата.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}, ...]
            model: ID модели для использования
            temperature: Температура сэмплирования (0.0-1.0)
            max_tokens: Максимальное количество токенов для генерации
            
        Returns:
            Результат генерации в формате словаря
        """
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            return self._make_request("/chat/completions", data=data)
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа в чате: {str(e)}")
            return {"error": str(e)}
    
    def generate_embeddings(self, texts: List[str], model: str = "text-embedding-ada-002") -> Dict:
        """
        Генерирует эмбеддинги для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга
            model: ID модели для генерации эмбеддингов
            
        Returns:
            Словарь с векторами эмбеддингов
        """
        data = {
            "model": model,
            "input": texts
        }
        
        try:
            return self._make_request("/embeddings", data=data)
        except Exception as e:
            logger.error(f"Ошибка при генерации эмбеддингов: {str(e)}")
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """
        Проверяет доступность API.
        
        Returns:
            True, если API доступен, иначе False
        """
        try:
            self._make_request("/models", method="GET")
            return True
        except Exception:
            return False


# Пример использования
if __name__ == "__main__":
    # Пример использования прокси для внешнего API
    proxy = ExternalLLMProxy(api_url="http://192.168.2.74:3131/v1")
    
    # Проверка доступности API
    if proxy.health_check():
        print("API доступен!")
        
        # Получение списка моделей
        models = proxy.get_models()
        print(f"Доступные модели: {json.dumps(models, indent=2)}")
        
        # Генерация текста
        result = proxy.generate_completion(
            prompt="Напиши короткое стихотворение о программировании",
            max_tokens=100
        )
        
        print("Результат генерации:")
        if "error" not in result:
            print(result.get("choices", [{}])[0].get("text", ""))
        else:
            print(f"Ошибка: {result['error']}")
    else:
        print("API недоступен!")