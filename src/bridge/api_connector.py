#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Коннектор API
============================

Модуль для взаимодействия с внешними API.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import os
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)


class APIConnector:
    """
    Класс для взаимодействия с внешними API.
    
    Управляет соединениями с различными API, обрабатывает запросы
    и ответы, а также обеспечивает обработку ошибок.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует коннектор API.
        
        Args:
            config: Конфигурация коннектора API
        """
        self.config = config or {}
        self.connections = {}  # Словарь активных соединений
        self.endpoints = self.config.get("endpoints", {})  # Конфигурация точек доступа API
        
        logger.info("Коннектор API инициализирован")
    
    def connect(self, api_name: str, api_config: Dict[str, Any]) -> bool:
        """
        Устанавливает соединение с API.
        
        Args:
            api_name: Имя API для идентификации
            api_config: Конфигурация API
            
        Returns:
            bool: True, если соединение успешно установлено, иначе False
        """
        if api_name in self.connections:
            logger.warning(f"Соединение с API '{api_name}' уже установлено")
            return True
        
        url = api_config.get("url", "")
        if not url:
            logger.error(f"URL для API '{api_name}' не указан")
            return False
        
        auth_required = api_config.get("auth_required", False)
        auth_type = api_config.get("auth_type", "")
        auth_token = api_config.get("auth_token", "")
        
        # Создаем настройки для соединения
        connection_config = {
            "url": url,
            "auth_required": auth_required,
            "auth_type": auth_type,
            "auth_token": auth_token,
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": "GC-Forged-Pylot/0.1.0"
            }
        }
        
        # Добавляем авторизацию, если требуется
        if auth_required and auth_type == "token" and auth_token:
            connection_config["headers"]["Authorization"] = f"Bearer {auth_token}"
        
        # Проверяем соединение
        try:
            response = requests.get(url, headers=connection_config["headers"], timeout=5)
            if response.status_code >= 400:
                logger.warning(f"API '{api_name}' вернул код {response.status_code}")
            else:
                logger.info(f"Соединение с API '{api_name}' успешно установлено")
            
            # Сохраняем соединение даже при ошибке, чтобы можно было использовать
            self.connections[api_name] = connection_config
            return True
        except Exception as e:
            logger.error(f"Ошибка при установке соединения с API '{api_name}': {str(e)}")
            # Сохраняем соединение даже при ошибке
            self.connections[api_name] = connection_config
            return False
    
    def disconnect(self, api_name: str) -> bool:
        """
        Закрывает соединение с API.
        
        Args:
            api_name: Имя API
            
        Returns:
            bool: True, если соединение закрыто успешно, иначе False
        """
        if api_name not in self.connections:
            logger.warning(f"Соединение с API '{api_name}' не установлено")
            return False
        
        try:
            # Удаляем соединение из словаря соединений
            del self.connections[api_name]
            logger.info(f"Соединение с API '{api_name}' закрыто")
            return True
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения с API '{api_name}': {str(e)}")
            return False
    
    def disconnect_all(self) -> None:
        """Закрывает все активные соединения."""
        api_names = list(self.connections.keys())
        for api_name in api_names:
            self.disconnect(api_name)
    
    def make_request(self, api_name: str, endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Dict[str, Any]:
        """
        Выполняет запрос к API.
        
        Args:
            api_name: Имя API
            endpoint: Конечная точка API
            method: HTTP-метод (GET, POST, PUT, DELETE)
            data: Данные для отправки в теле запроса
            params: Параметры URL
            
        Returns:
            Dict[str, Any]: Результат запроса
            
        Raises:
            Exception: При ошибке выполнения запроса
        """
        if api_name not in self.connections:
            raise Exception(f"Соединение с API '{api_name}' не установлено")
        
        connection = self.connections[api_name]
        url = connection["url"]
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = url.rstrip("/") + endpoint
        
        headers = connection.get("headers", {})
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Неподдерживаемый HTTP-метод: {method}")
            
            elapsed_time = time.time() - start_time
            
            result = {
                "status_code": response.status_code,
                "elapsed_time": elapsed_time,
                "headers": dict(response.headers)
            }
            
            # Добавляем данные ответа, если есть
            try:
                result["data"] = response.json()
            except ValueError:
                result["text"] = response.text
            
            # Проверяем код состояния
            if response.status_code >= 400:
                logger.error(f"Ошибка при запросе к {url}: код {response.status_code}")
                result["success"] = False
                result["error"] = f"HTTP error {response.status_code}"
            else:
                result["success"] = True
            
            return result
        except Exception as e:
            logger.error(f"Ошибка при запросе к {url}: {str(e)}")
            raise
    
    def list_connected_apis(self) -> List[str]:
        """
        Возвращает список подключенных API.
        
        Returns:
            List[str]: Список имен подключенных API
        """
        return list(self.connections.keys())