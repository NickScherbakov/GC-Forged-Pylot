#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - VS Code Integration
====================================

Module for interacting with VS Code through Language Server Protocol (LSP).
Provides code completion functionality and other IDE features.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import json
import logging
import threading
import asyncio
import websockets
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from pathlib import Path
import socket
import uuid
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VSCodeIntegration")


class LspMessage:
    """
    Класс для работы с сообщениями в формате Language Server Protocol.
    """
    
    @staticmethod
    def create_request(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает сообщение-запрос LSP.
        
        Args:
            method: Метод LSP
            params: Параметры запроса
            
        Returns:
            Dict[str, Any]: Запрос LSP
        """
        return {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params
        }
    
    @staticmethod
    def create_response(id: str, result: Any) -> Dict[str, Any]:
        """
        Создает сообщение-ответ LSP.
        
        Args:
            id: ID запроса
            result: Результат запроса
            
        Returns:
            Dict[str, Any]: Ответ LSP
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": result
        }
    
    @staticmethod
    def create_error(id: str, code: int, message: str) -> Dict[str, Any]:
        """
        Создает сообщение об ошибке LSP.
        
        Args:
            id: ID запроса
            code: Код ошибки
            message: Сообщение об ошибке
            
        Returns:
            Dict[str, Any]: Ошибка LSP
        """
        return {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    @staticmethod
    def create_notification(method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Создает уведомление LSP.
        
        Args:
            method: Метод LSP
            params: Параметры уведомления
            
        Returns:
            Dict[str, Any]: Уведомление LSP
        """
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }


class CompletionProvider:
    """
    Провайдер автодополнений для VS Code.
    """
    
    def __init__(self, llm_client):
        """
        Инициализирует провайдер.
        
        Args:
            llm_client: Клиент языковой модели
        """
        self.llm_client = llm_client
        self.language_map = {
            "python": "python",
            "javascript": "javascript", 
            "typescript": "typescript",
            "cpp": "c++",
            "c": "c",
            "csharp": "c#",
            "java": "java",
            "php": "php",
            "ruby": "ruby",
            "rust": "rust",
            "go": "go",
            "html": "html",
            "css": "css",
            "json": "json",
            "markdown": "markdown",
        }
    
    async def provide_completions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Предоставляет автодополнения.
        
        Args:
            params: Параметры запроса
            
        Returns:
            List[Dict[str, Any]]: Список автодополнений
        """
        try:
            # Извлекаем необходимую информацию из параметров
            document_uri = params.get("textDocument", {}).get("uri", "")
            position = params.get("position", {})
            line = position.get("line", 0)
            character = position.get("character", 0)
            context = params.get("context", {})
            trigger_kind = context.get("triggerKind", 1)  # 1 - Invoked, 2 - TriggerCharacter
            trigger_character = context.get("triggerCharacter", "")
            
            # Получаем содержимое документа
            document_content = params.get("textDocument", {}).get("text", "")
            if not document_content:
                # Если текст не предоставлен, пытаемся прочитать файл
                try:
                    file_path = self._uri_to_path(document_uri)
                    with open(file_path, "r", encoding="utf-8") as f:
                        document_content = f.read()
                except Exception as e:
                    logger.error(f"Не удалось прочитать содержимое документа: {e}")
                    return []
            
            # Определяем язык программирования
            language_id = params.get("textDocument", {}).get("languageId", "")
            if not language_id:
                # Определяем язык по расширению файла
                file_path = self._uri_to_path(document_uri)
                file_ext = os.path.splitext(file_path)[1].lower()
                language_id = {
                    ".py": "python",
                    ".js": "javascript",
                    ".ts": "typescript",
                    ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp", ".h": "cpp",
                    ".c": "c",
                    ".cs": "csharp",
                    ".java": "java",
                    ".php": "php",
                    ".rb": "ruby",
                    ".rs": "rust",
                    ".go": "go",
                    ".html": "html", ".htm": "html",
                    ".css": "css",
                    ".json": "json",
                    ".md": "markdown"
                }.get(file_ext, "plaintext")
            
            # Разбиваем текст на строки и получаем текущую строку
            lines = document_content.split("\n")
            current_line = lines[line] if line < len(lines) else ""
            
            # Получаем текст до курсора
            text_before_cursor = current_line[:character]
            
            # Формируем контекст для запроса к LLM
            context_lines_before = 10
            context_lines_after = 5
            
            start_line = max(0, line - context_lines_before)
            end_line = min(len(lines), line + context_lines_after + 1)
            
            context_before = "\n".join(lines[start_line:line])
            context_after = "\n".join(lines[line+1:end_line])
            
            # Формируем промпт для языковой модели
            language = self.language_map.get(language_id, language_id)
            prompt = f"""Я работаю с кодом на языке {language}. 
Предоставь автодополнение для следующего кода:

```{language}
{context_before}
{text_before_cursor}|КУРСОР|{current_line[character:]}
{context_after}
```

Предложи 3-5 вариантов автодополнения, начиная от текущей позиции курсора.
Верни только текст автодополнения без кавычек или форматирования, разделяя варианты символом '|||'.
"""
            
            # Получаем предсказание от языковой модели
            completion_result = await self._get_completions_from_llm(prompt, language_id)
            if not completion_result:
                return []
                
            # Разбираем результат
            completion_options = completion_result.strip().split("|||")
            
            # Преобразуем в формат VS Code CompletionItem
            completion_items = []
            for i, option in enumerate(completion_options):
                option = option.strip()
                if not option:
                    continue
                    
                # Определяем тип элемента (функция, переменная и т.д.)
                item_kind = self._determine_item_kind(option)
                
                # Создаем элемент дополнения
                completion_items.append({
                    "label": option[:40] + ("..." if len(option) > 40 else ""),
                    "kind": item_kind,
                    "detail": f"GC-Forged Pylot предлагает: {option[:100]}{'...' if len(option) > 100 else ''}",
                    "documentation": {
                        "kind": "markdown",
                        "value": f"```{language_id}\n{option}\n```"
                    },
                    "insertText": option,
                    "data": {
                        "language": language_id,
                        "proposal": option
                    }
                })
                
            return completion_items
            
        except Exception as e:
            logger.error(f"Ошибка при формировании автодополнений: {str(e)}")
            return []
    
    async def _get_completions_from_llm(self, prompt: str, language_id: str) -> str:
        """
        Получает автодополнения от языковой модели.
        
        Args:
            prompt: Промпт для языковой модели
            language_id: Идентификатор языка
            
        Returns:
            str: Текст автодополнения
        """
        try:
            # Выполняем запрос к языковой модели
            response = await self.llm_client.generate_async(
                prompt=prompt,
                max_tokens=256,
                temperature=0.2,  # Низкая температура для более точных предсказаний
                top_p=0.95
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Ошибка при получении автодополнений от LLM: {str(e)}")
            return ""
    
    def _determine_item_kind(self, text: str) -> int:
        """
        Определяет тип элемента автодополнения.
        
        Args:
            text: Текст автодополнения
            
        Returns:
            int: Тип элемента в соответствии с VSCode.CompletionItemKind
        """
        # VSCode.CompletionItemKind:
        # 1: Text, 2: Method, 3: Function, 4: Constructor, 5: Field, 6: Variable,
        # 7: Class, 8: Interface, 9: Module, 10: Property, 11: Unit, 12: Value,
        # 13: Enum, 14: Keyword, 15: Snippet, 16: Color, 17: File, 18: Reference,
        # 19: Folder, 20: EnumMember, 21: Constant, 22: Struct, 23: Event,
        # 24: Operator, 25: TypeParameter
        
        text = text.strip()
        
        # Функция или метод (начинается с def, function, или содержит () {})
        if text.startswith("def ") or text.startswith("function ") or \
           ("(" in text and ")" in text):
            return 3  # Function
            
        # Класс
        if text.startswith("class "):
            return 7  # Class
            
        # Импорт/модуль
        if text.startswith("import ") or text.startswith("from "):
            return 9  # Module
            
        # Переменная (присваивание)
        if " = " in text:
            return 6  # Variable
            
        # По умолчанию - текст
        return 1  # Text
    
    def _uri_to_path(self, uri: str) -> str:
        """
        Преобразует URI в путь к файлу.
        
        Args:
            uri: URI файла
            
        Returns:
            str: Путь к файлу
        """
        if uri.startswith("file://"):
            if sys.platform == "win32":
                # Для Windows: file:///c:/path -> c:\\path
                path = uri[8:].replace("/", "\\")
                return path
            else:
                # Для Unix: file:///path -> /path
                return uri[7:]
        return uri


class VSCodeLanguageServer:
    """
    Сервер языка для VS Code, реализующий Language Server Protocol.
    """
    
    def __init__(self, llm_client, server_config: Dict[str, Any] = None):
        """
        Инициализирует сервер.
        
        Args:
            llm_client: Клиент языковой модели
            server_config: Конфигурация сервера
        """
        self.config = server_config or {}
        self.llm_client = llm_client
        self.completion_provider = CompletionProvider(llm_client)
        self.initialized = False
        self.workspaces = {}  # Рабочие области
        self.documents = {}   # Открытые документы
        self.capabilities = {}  # Возможности клиента
        self.port = self.config.get("port", 0)  # 0 = автоматический выбор порта
        self.host = self.config.get("host", "127.0.0.1")
        self.server = None
        self.is_running = False
        self.clients = set()  # Подключенные клиенты
        
        # Обработчики методов
        self.handlers = {
            "initialize": self.handle_initialize,
            "initialized": self.handle_initialized,
            "textDocument/didOpen": self.handle_text_document_did_open,
            "textDocument/didChange": self.handle_text_document_did_change,
            "textDocument/didClose": self.handle_text_document_did_close,
            "textDocument/completion": self.handle_text_document_completion,
            "shutdown": self.handle_shutdown,
            "exit": self.handle_exit
        }
        
        logger.info("VS Code Language Server инициализирован")
    
    async def start_server(self):
        """
        Запускает сервер.
        
        Returns:
            int: Порт, на котором запущен сервер
        """
        if self.is_running:
            logger.warning("Сервер уже запущен")
            return self.port
        
        try:
            # Запускаем WebSocket сервер
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            
            # Определяем фактический порт
            for sock in self.server.sockets:
                if self.port == 0:
                    self.port = sock.getsockname()[1]
                    break
            
            self.is_running = True
            logger.info(f"VS Code Language Server запущен на {self.host}:{self.port}")
            
            # Запускаем сообщение о доступности сервера
            self._announce_server()
            
            return self.port
            
        except Exception as e:
            logger.error(f"Ошибка при запуске сервера: {str(e)}")
            raise
    
    def _announce_server(self):
        """
        Создает файл объявления сервера для VS Code.
        """
        try:
            # Создаем временный файл с информацией о сервере
            announcement_file = os.path.join(
                os.path.expanduser("~"),
                ".gc-forged-pylot",
                "server-info.json"
            )
            
            os.makedirs(os.path.dirname(announcement_file), exist_ok=True)
            
            server_info = {
                "protocol": "websocket",
                "host": self.host,
                "port": self.port,
                "pid": os.getpid(),
                "startTime": datetime.now().isoformat()
            }
            
            with open(announcement_file, "w") as f:
                json.dump(server_info, f)
                
            logger.info(f"Информация о сервере сохранена в {announcement_file}")
            
        except Exception as e:
            logger.error(f"Ошибка при создании файла объявления сервера: {str(e)}")
    
    async def stop_server(self):
        """
        Останавливает сервер.
        """
        if not self.is_running:
            logger.warning("Сервер не запущен")
            return
        
        try:
            # Закрываем все подключения
            for client in list(self.clients):
                try:
                    await client.close()
                except:
                    pass
            self.clients.clear()
            
            # Останавливаем сервер
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                self.server = None
            
            self.is_running = False
            logger.info("VS Code Language Server остановлен")
            
        except Exception as e:
            logger.error(f"Ошибка при остановке сервера: {str(e)}")
    
    async def handle_client(self, websocket, path):
        """
        Обрабатывает подключение клиента.
        
        Args:
            websocket: WebSocket соединение
            path: Путь запроса
        """
        self.clients.add(websocket)
        logger.info(f"Новое подключение клиента: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    # Разбираем сообщение JSON-RPC
                    request = json.loads(message)
                    
                    # Обрабатываем запрос
                    response = await self.handle_message(request)
                    
                    # Отправляем ответ, если он есть
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    logger.error("Получено некорректное JSON-сообщение")
                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Соединение закрыто: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает входящее сообщение LSP.
        
        Args:
            message: Сообщение LSP
            
        Returns:
            Optional[Dict[str, Any]]: Ответное сообщение LSP, если требуется
        """
        # Проверяем, это запрос, уведомление или ответ
        if "method" in message:
            # Это запрос или уведомление
            method = message.get("method", "")
            id = message.get("id")
            params = message.get("params", {})
            
            # Находим обработчик метода
            handler = self.handlers.get(method)
            if handler:
                try:
                    result = await handler(params)
                    
                    # Если есть id, это запрос, на который нужно ответить
                    if id is not None:
                        return LspMessage.create_response(id, result)
                    
                    # Если нет id, это уведомление, на которое не нужно отвечать
                    return None
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке метода {method}: {str(e)}")
                    if id is not None:
                        return LspMessage.create_error(id, -32603, f"Внутренняя ошибка сервера: {str(e)}")
            else:
                logger.warning(f"Неизвестный метод LSP: {method}")
                if id is not None:
                    return LspMessage.create_error(id, -32601, f"Метод не найден: {method}")
        else:
            # Это ответ, не требует обработки
            pass
            
        return None
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает инициализацию клиента.
        
        Args:
            params: Параметры инициализации
            
        Returns:
            Dict[str, Any]: Результат инициализации
        """
        self.capabilities = params.get("capabilities", {})
        
        # Сохраняем информацию о рабочей области
        root_uri = params.get("rootUri")
        workspace_folders = params.get("workspaceFolders", [])
        
        if root_uri:
            self.workspaces[root_uri] = {
                "uri": root_uri,
                "name": os.path.basename(self._uri_to_path(root_uri)),
                "documents": {}
            }
            
        for folder in workspace_folders:
            folder_uri = folder.get("uri")
            if folder_uri:
                self.workspaces[folder_uri] = {
                    "uri": folder_uri,
                    "name": folder.get("name", os.path.basename(self._uri_to_path(folder_uri))),
                    "documents": {}
                }
        
        # Возвращаем возможности сервера
        return {
            "capabilities": {
                "textDocumentSync": {
                    "openClose": True,
                    "change": 2,  # Incremental
                    "willSave": False,
                    "willSaveWaitUntil": False,
                    "save": {
                        "includeText": False
                    }
                },
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": ["."]
                },
                "workspace": {
                    "workspaceFolders": {
                        "supported": True,
                        "changeNotifications": True
                    }
                }
            },
            "serverInfo": {
                "name": "GC-Forged-Pylot LSP Server",
                "version": "1.0.0"
            }
        }
    
    async def handle_initialized(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает уведомление об успешной инициализации.
        
        Args:
            params: Параметры уведомления
        """
        self.initialized = True
        logger.info("Клиент инициализирован")
        
        # Отправляем уведомление о готовности сервера
        # Это может быть использовано для отображения сообщения в VS Code
        for client in self.clients:
            try:
                notification = LspMessage.create_notification(
                    "window/showMessage",
                    {
                        "type": 3,  # MessageType.Info = 3
                        "message": "GC-Forged-Pylot Language Server готов к работе!"
                    }
                )
                await client.send(json.dumps(notification))
            except:
                pass
    
    async def handle_text_document_did_open(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает открытие документа.
        
        Args:
            params: Параметры уведомления
        """
        document = params.get("textDocument", {})
        uri = document.get("uri")
        text = document.get("text", "")
        language_id = document.get("languageId", "")
        
        if uri:
            self.documents[uri] = {
                "uri": uri,
                "text": text,
                "languageId": language_id,
                "version": document.get("version", 1)
            }
            
            logger.debug(f"Документ открыт: {uri}")
    
    async def handle_text_document_did_change(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает изменение документа.
        
        Args:
            params: Параметры уведомления
        """
        document_uri = params.get("textDocument", {}).get("uri")
        changes = params.get("contentChanges", [])
        
        if document_uri in self.documents:
            # TODO: Реализовать инкрементальное обновление текста
            # Пока просто заменяем весь текст, если есть полное содержимое
            if changes and "text" in changes[0]:
                self.documents[document_uri]["text"] = changes[0]["text"]
                logger.debug(f"Документ изменен: {document_uri}")
    
    async def handle_text_document_did_close(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает закрытие документа.
        
        Args:
            params: Параметры уведомления
        """
        document_uri = params.get("textDocument", {}).get("uri")
        
        if document_uri in self.documents:
            del self.documents[document_uri]
            logger.debug(f"Документ закрыт: {document_uri}")
    
    async def handle_text_document_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает запрос автодополнения.
        
        Args:
            params: Параметры запроса
            
        Returns:
            Dict[str, Any]: Список элементов автодополнения
        """
        # Добавляем информацию о документе из нашего кэша
        document_uri = params.get("textDocument", {}).get("uri")
        
        if document_uri in self.documents:
            params["textDocument"]["text"] = self.documents[document_uri]["text"]
            params["textDocument"]["languageId"] = self.documents[document_uri]["languageId"]
        
        # Получаем автодополнения
        completion_items = await self.completion_provider.provide_completions(params)
        
        return {
            "isIncomplete": False,
            "items": completion_items
        }
    
    async def handle_shutdown(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает запрос на завершение работы.
        
        Args:
            params: Параметры запроса
        """
        logger.info("Получен запрос на завершение работы")
        self.initialized = False
        return None
    
    async def handle_exit(self, params: Dict[str, Any]) -> None:
        """
        Обрабатывает запрос на выход.
        
        Args:
            params: Параметры запроса
        """
        logger.info("Получен запрос на выход")
        await self.stop_server()
        return None
    
    def _uri_to_path(self, uri: str) -> str:
        """
        Преобразует URI в путь к файлу.
        
        Args:
            uri: URI файла
            
        Returns:
            str: Путь к файлу
        """
        if uri.startswith("file://"):
            if sys.platform == "win32":
                # Для Windows: file:///c:/path -> c:\\path
                path = uri[8:].replace("/", "\\")
                return path
            else:
                # Для Unix: file:///path -> /path
                return uri[7:]
        return uri


class VSCodeExtensionConnector:
    """
    Коннектор для взаимодействия с VS Code расширением.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует коннектор.
        
        Args:
            config: Конфигурация коннектора
        """
        self.config = config or {}
        self.language_server = None
        self.llm_client = None
        self.server_thread = None
        self.server_port = None
        
        logger.info("VS Code Extension Connector инициализирован")
    
    def setup(self, llm_client):
        """
        Настраивает коннектор с экземпляром LLM клиента.
        
        Args:
            llm_client: Клиент языковой модели
        """
        self.llm_client = llm_client
        
        # Создаем языковой сервер
        server_config = self.config.get("language_server", {})
        self.language_server = VSCodeLanguageServer(llm_client, server_config)
        
        logger.info("VS Code Extension Connector настроен")
    
    async def start_language_server_async(self) -> int:
        """
        Запускает языковой сервер асинхронно.
        
        Returns:
            int: Порт, на котором запущен сервер
        """
        if not self.language_server:
            raise ValueError("Языковой сервер не настроен. Вызовите setup() сначала.")
        
        self.server_port = await self.language_server.start_server()
        return self.server_port
    
    def start_language_server(self) -> int:
        """
        Запускает языковой сервер в отдельном потоке.
        
        Returns:
            int: Порт, на котором запущен сервер
        """
        if not self.language_server:
            raise ValueError("Языковой сервер не настроен. Вызовите setup() сначала.")
            
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("Языковой сервер уже запущен")
            return self.server_port
        
        # Создаем и запускаем новый поток для сервера
        loop = asyncio.new_event_loop()
        
        def run_server():
            asyncio.set_event_loop(loop)
            self.server_port = loop.run_until_complete(self.language_server.start_server())
            loop.run_forever()
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Ждем немного, чтобы сервер запустился
        import time
        time.sleep(0.5)
        
        return self.server_port
    
    def stop_language_server(self):
        """
        Останавливает языковой сервер.
        """
        if not self.server_thread or not self.server_thread.is_alive():
            logger.warning("Языковой сервер не запущен")
            return
            
        # Останавливаем сервер
        if hasattr(self, 'language_server') and self.language_server:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self.language_server.stop_server())
        
        # Останавливаем поток
        if hasattr(self, 'server_thread') and self.server_thread:
            try:
                self.server_thread.join(timeout=2.0)
            except:
                pass
            self.server_thread = None
        
        logger.info("Языковой сервер остановлен")
    
    def get_server_connection_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о подключении к серверу.
        
        Returns:
            Dict[str, Any]: Информация о подключении
        """
        if not self.server_port:
            return {"error": "Сервер не запущен"}
            
        return {
            "protocol": "websocket",
            "host": self.language_server.host,
            "port": self.server_port,
            "pid": os.getpid()
        }


if __name__ == "__main__":
    # Тестирование модуля
    from concurrent.futures import ThreadPoolExecutor
    import time
    
    class DummyLLMClient:
        async def generate_async(self, prompt, **kwargs):
            class Response:
                def __init__(self, text):
                    self.text = text
            
            print(f"Запрос к LLM: {prompt[:50]}...")
            return Response("print('Hello, world!')||| def calculate_sum(a, b):\n    return a + b ||| for i in range(10):")
    
    async def main():
        # Создаем фиктивный LLM клиент
        llm_client = DummyLLMClient()
        
        # Создаем и запускаем языковой сервер
        server = VSCodeLanguageServer(llm_client)
        port = await server.start_server()
        
        print(f"Сервер запущен на порту {port}")
        
        # Даем серверу поработать
        await asyncio.sleep(60)
        
        # Останавливаем сервер
        await server.stop_server()
    
    # Запускаем асинхронный код
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Прервано пользователем")