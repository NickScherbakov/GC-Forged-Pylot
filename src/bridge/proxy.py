#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Proxy for External APIs
========================================

Module for interacting with external language model APIs.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import json
import logging
import requests
import time
import asyncio
import aiohttp
import backoff
from typing import Dict, List, Any, Optional, Union, Callable, Generator, AsyncGenerator
from urllib.parse import urljoin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("ExternalLLMProxy")


class ExternalLLMProxy:
    """
    Прокси для взаимодействия с внешними API языковых моделей.
    
    Позволяет подключаться к внешним API, таким как Ollama, llama.cpp или другие
    совместимые с OpenAI API сервисы.
    """
    
    def __init__(self, 
                api_url: str, 
                api_key: str = None, 
                timeout: int = 60,
                connection_retries: int = 3,
                connection_retry_delay: float = 0.5,
                verify_ssl: bool = True):
        """
        Инициализирует прокси для внешнего API.
        
        Args:
            api_url: URL API, например "http://192.168.2.74:3131/v1"
            api_key: Ключ API для авторизации (если требуется)
            timeout: Таймаут для запросов в секундах
            connection_retries: Количество повторных попыток при сбоях сети
            connection_retry_delay: Задержка между повторными попытками в секундах
            verify_ssl: Проверять ли SSL-сертификаты (отключать только для тестирования)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.connection_retries = connection_retries
        self.connection_retry_delay = connection_retry_delay
        self.verify_ssl = verify_ssl
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
        # Создание сессии для эффективного переиспользования соединений
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = verify_ssl
        
        logger.info(f"Инициализация прокси для внешнего API: {self.api_url}")
    
    @backoff.on_exception(backoff.expo, 
                        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
                        max_tries=3)
    def _make_request(self, endpoint: str, method: str = "POST", data: Dict = None) -> Dict:
        """
        Выполняет запрос к внешнему API с автоматическим повтором при сбоях.
        
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
                response = self.session.get(url, timeout=self.timeout)
            else:  # Default to POST
                response = self.session.post(url, json=data, timeout=self.timeout)
            
            elapsed = time.time() - start_time
            logger.debug(f"Запрос к {url} выполнен за {elapsed:.2f}с")
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"Ошибка API ({response.status_code}): {response.text}"
                logger.error(error_msg)
                return {"error": error_msg, "status_code": response.status_code}
                
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
            if "error" in response:
                logger.error(f"Ошибка при получении списка моделей: {response['error']}")
                return []
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
                           top_k: int = 40,
                           repeat_penalty: float = 1.1,
                           stream: bool = False,
                           stop: List[str] = None) -> Union[Dict, Generator]:
        """
        Генерирует текстовое завершение на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации
            model: ID модели для использования
            max_tokens: Максимальное количество токенов для генерации
            temperature: Температура сэмплирования (0.0-1.0)
            top_p: Параметр nucleus sampling (0.0-1.0)
            top_k: Параметр top-k sampling
            repeat_penalty: Штраф за повторение
            stream: Использовать ли потоковую генерацию
            stop: Список стоп-последовательностей
            
        Returns:
            Результат генерации в формате словаря или генератор для потоковой генерации
        """
        data = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "stream": stream
        }
        
        if stop:
            data["stop"] = stop
            
        try:
            if stream:
                return self._stream_completion(data)
            else:
                return self._make_request("/completions", data=data)
        except Exception as e:
            logger.error(f"Ошибка при генерации завершения: {str(e)}")
            return {"error": str(e)}
    
    def _stream_completion(self, data: Dict) -> Generator:
        """
        Создает генератор для потоковой генерации текста.
        
        Args:
            data: Параметры запроса
            
        Yields:
            Фрагменты текста по мере их генерации
        """
        url = f"{self.api_url}/completions"
        
        try:
            with self.session.post(url, json=data, stream=True, timeout=self.timeout) as response:
                if response.status_code != 200:
                    error_msg = f"Ошибка API ({response.status_code}): {response.text}"
                    logger.error(error_msg)
                    yield {"error": error_msg}
                    return
                    
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        
                        # Пропускаем пустые строки и строки keep-alive
                        if not line or line == "data: [DONE]":
                            continue
                            
                        # Разбираем формат SSE (Server-Sent Events)
                        if line.startswith('data: '):
                            try:
                                json_str = line[6:]  # Убираем 'data: '
                                data = json.loads(json_str)
                                yield data
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка разбора JSON в потоковом ответе: {e}")
                                yield {"error": "JSON decode error", "raw": line}
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при потоковой генерации: {e}")
            yield {"error": f"Connection error: {e}"}
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Таймаут при потоковой генерации: {e}")
            yield {"error": f"Timeout error: {e}"}
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при потоковой генерации: {e}")
            yield {"error": f"Error: {e}"}
    
    async def async_generate_completion(self,
                                       prompt: str,
                                       model: str = "gpt-3.5-turbo-instruct",
                                       max_tokens: int = 256,
                                       temperature: float = 0.7,
                                       top_p: float = 0.95,
                                       stream: bool = False) -> Union[Dict, AsyncGenerator]:
        """
        Асинхронно генерирует текстовое завершение на основе промпта.
        
        Args:
            prompt: Текстовый промпт для генерации
            model: ID модели для использования
            max_tokens: Максимальное количество токенов для генерации
            temperature: Температура сэмплирования (0.0-1.0)
            top_p: Параметр nucleus sampling (0.0-1.0)
            stream: Использовать ли потоковую генерацию
            
        Returns:
            Результат генерации в формате словаря или асинхронный генератор
        """
        data = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }
        
        url = f"{self.api_url}/completions"
        headers = self.headers.copy()
        
        async with aiohttp.ClientSession() as session:
            if stream:
                return self._async_stream_completion(session, url, data, headers)
            
            try:
                async with session.post(url, json=data, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API ({response.status}): {error_text}")
                        return {"error": f"API Error ({response.status}): {error_text}"}
            except Exception as e:
                logger.error(f"Ошибка асинхронной генерации: {e}")
                return {"error": str(e)}
    
    async def _async_stream_completion(self, session, url, data, headers) -> AsyncGenerator:
        """
        Асинхронный генератор для потоковой генерации.
        
        Args:
            session: Сессия aiohttp
            url: URL для запроса
            data: Данные запроса
            headers: HTTP-заголовки
            
        Yields:
            Фрагменты текста по мере их генерации
        """
        try:
            async with session.post(url, json=data, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ошибка API при потоковой генерации ({response.status}): {error_text}")
                    yield {"error": f"API Error ({response.status}): {error_text}"}
                    return
                
                async for line in response.content:
                    line = line.decode('utf-8')
                    
                    # Пропускаем пустые строки и разделители
                    if not line.strip() or line == 'data: [DONE]':
                        continue
                        
                    if line.startswith('data: '):
                        try:
                            json_str = line[6:]
                            data = json.loads(json_str)
                            yield data
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка разбора JSON в асинхронном потоковом ответе: {e}")
                            yield {"error": "JSON decode error", "raw": line}
                            
        except asyncio.TimeoutError:
            logger.error(f"Асинхронный таймаут при потоковой генерации")
            yield {"error": "Timeout error during streaming"}
            
        except Exception as e:
            logger.error(f"Ошибка при асинхронной потоковой генерации: {e}")
            yield {"error": str(e)}
    
    def generate_chat_completion(self, 
                                messages: List[Dict[str, str]], 
                                model: str = "gpt-3.5-turbo",
                                temperature: float = 0.7,
                                max_tokens: int = 256,
                                top_p: float = 0.95,
                                stream: bool = False,
                                stop: List[str] = None) -> Union[Dict, Generator]:
        """
        Генерирует ответ на основе истории сообщений в формате чата.
        
        Args:
            messages: Список сообщений в формате [{role: "user", content: "текст"}, ...]
            model: ID модели для использования
            temperature: Температура сэмплирования (0.0-1.0)
            max_tokens: Максимальное количество токенов для генерации
            top_p: Параметр nucleus sampling (0.0-1.0)
            stream: Использовать ли потоковую генерацию
            stop: Список стоп-последовательностей
            
        Returns:
            Результат генерации или генератор для потоковой генерации
        """
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": stream
        }
        
        if stop:
            data["stop"] = stop
        
        try:
            if stream:
                return self._stream_chat_completion(data)
            else:
                return self._make_request("/chat/completions", data=data)
        except Exception as e:
            logger.error(f"Ошибка при генерации ответа в чате: {str(e)}")
            return {"error": str(e)}
    
    def _stream_chat_completion(self, data: Dict) -> Generator:
        """
        Создает генератор для потоковой генерации чата.
        
        Args:
            data: Параметры запроса
            
        Yields:
            Фрагменты ответа по мере их генерации
        """
        url = f"{self.api_url}/chat/completions"
        
        try:
            with self.session.post(url, json=data, stream=True, timeout=self.timeout) as response:
                if response.status_code != 200:
                    error_msg = f"Ошибка API ({response.status_code}): {response.text}"
                    logger.error(error_msg)
                    yield {"error": error_msg}
                    return
                    
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        
                        if not line or line == "data: [DONE]":
                            continue
                            
                        if line.startswith('data: '):
                            try:
                                json_str = line[6:]
                                data = json.loads(json_str)
                                yield data
                            except json.JSONDecodeError as e:
                                logger.error(f"Ошибка разбора JSON в потоковом ответе чата: {e}")
                                yield {"error": "JSON decode error", "raw": line}
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ошибка соединения при потоковой генерации чата: {e}")
            yield {"error": f"Connection error: {e}"}
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Таймаут при потоковой генерации чата: {e}")
            yield {"error": f"Timeout error: {e}"}
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при потоковой генерации чата: {e}")
            yield {"error": f"Error: {e}"}
    
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
            response = self._make_request("/models", method="GET")
            return "error" not in response
        except Exception:
            return False
            
    def close(self):
        """
        Закрывает сессию и освобождает ресурсы.
        """
        try:
            self.session.close()
            logger.debug("Сессия API закрыта")
        except Exception as e:
            logger.warning(f"Ошибка при закрытии сессии API: {e}")


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
            
        # Пример потоковой генерации
        print("\nПример потоковой генерации:")
        try:
            for chunk in proxy.generate_completion(
                prompt="Объясни, как работает машинное обучение",
                max_tokens=50,
                stream=True
            ):
                if "error" not in chunk:
                    text = chunk.get("choices", [{}])[0].get("text", "")
                    print(text, end="", flush=True)
                else:
                    print(f"\nОшибка потоковой генерации: {chunk['error']}")
            print("\n")
        except Exception as e:
            print(f"Ошибка при демонстрации потоковой генерации: {e}")
    else:
        print("API недоступен!")