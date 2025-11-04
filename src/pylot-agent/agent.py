#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot Agent
=====================

Main module of the autonomous agent for the GC-Forged Pylot system.
The agent integrates core system components and bridge for interaction
with external systems and APIs.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import logging
import argparse
import json
from typing import Dict, List, Any, Optional, Union, Tuple

# Добавляем путь к родительскому каталогу в sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорт компонентов ядра
from core.executor import Executor
from core.memory import Memory
from core.planner import Planner
from core.reasoning import Reasoner
from core.llm_interface import LLMInterface
from core.llm_llama_cpp import LLamaLLM
from core.llm_external import ExternalLLMAdapter

# Импорт компонентов моста
from bridge.api_connector import APIConnector
from bridge.tool_manager import ToolManager
from bridge.feedback_handler import FeedbackHandler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pylot_agent.log")
    ]
)

logger = logging.getLogger("PylotAgent")


class PylotAgent:
    """
    Главный класс автономного агента GC-Forged Pylot.
    
    Агент объединяет различные компоненты системы для обеспечения
    интеллектуального взаимодействия с пользователем и внешними системами.
    """
    
    def __init__(self, config_path: str = "config/agent_config.json"):
        """
        Инициализирует агента с заданной конфигурацией.
        
        Args:
            config_path: Путь к файлу конфигурации агента в формате JSON.
        """
        logger.info("Инициализация агента Pylot...")
        self.config = self._load_config(config_path)
        
        # Инициализация LLM в зависимости от типа
        llm_config = self.config.get("llm", {})
        llm_type = llm_config.get("type", "llama_cpp")
        
        if llm_type == "external":
            logger.info("Инициализация внешнего LLM API...")
            self.llm = ExternalLLMAdapter(llm_config)
        else:
            logger.info("Инициализация локального LLM (llama.cpp)...")
            self.llm = LLamaLLM(llm_config)
        
        # Инициализация компонентов ядра
        self.memory = Memory(self.config.get("memory", {}))
        self.reasoner = Reasoner(self.llm, self.config.get("reasoning", {}))
        self.planner = Planner(self.llm, self.reasoner, self.config.get("planning", {}))
        self.executor = Executor(self.config.get("execution", {}))
        
        # Инициализация компонентов моста
        self.api_connector = APIConnector(self.config.get("api", {}))
        self.tool_manager = ToolManager(self.config.get("tools", {}))
        self.feedback_handler = FeedbackHandler(self.config.get("feedback", {}))
        
        # Состояние агента
        self.conversation_history = []
        self.current_plan = None
        self.active = False
        
        logger.info("Агент Pylot успешно инициализирован")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Загружает конфигурацию агента из JSON-файла.
        
        Args:
            config_path: Путь к файлу конфигурации.
            
        Returns:
            Словарь с параметрами конфигурации.
            
        Raises:
            FileNotFoundError: Если файл конфигурации не найден.
            json.JSONDecodeError: Если файл конфигурации содержит некорректный JSON.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Конфигурация загружена из {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Файл конфигурации {config_path} не найден. Используются параметры по умолчанию.")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Ошибка при разборе файла конфигурации {config_path}. Используются параметры по умолчанию.")
            return {}
    
    def start(self) -> None:
        """Запускает агента и подготавливает его к взаимодействию."""
        logger.info("Запуск агента Pylot")
        self.active = True
        self._load_tools()
        self._initialize_memory()
        self._connect_apis()
    
    def stop(self) -> None:
        """Останавливает агента и освобождает ресурсы."""
        logger.info("Остановка агента Pylot")
        self.active = False
        self._save_conversation_history()
        self._disconnect_apis()
        
        # Освобождаем ресурсы LLM
        if hasattr(self.llm, 'shutdown'):
            self.llm.shutdown()
    
    def _load_tools(self) -> None:
        """Загружает доступные инструменты для агента."""
        tool_configs = self.config.get("tools", {}).get("available_tools", [])
        for tool_config in tool_configs:
            self.tool_manager.register_tool(tool_config)
        logger.info(f"Загружено {len(tool_configs)} инструментов")
    
    def _initialize_memory(self) -> None:
        """Инициализирует систему памяти агента."""
        memory_type = self.config.get("memory", {}).get("type", "default")
        logger.info(f"Инициализация памяти типа '{memory_type}'")
        self.memory.initialize()
    
    def _connect_apis(self) -> None:
        """Устанавливает соединения с внешними API."""
        api_configs = self.config.get("api", {}).get("endpoints", {})
        for api_name, api_config in api_configs.items():
            self.api_connector.connect(api_name, api_config)
        logger.info(f"Установлено соединение с {len(api_configs)} API")
    
    def _disconnect_apis(self) -> None:
        """Закрывает соединения с внешними API."""
        self.api_connector.disconnect_all()
        logger.info("Все соединения с API закрыты")
    
    def _save_conversation_history(self) -> None:
        """Сохраняет историю взаимодействия с пользователем."""
        if self.conversation_history:
            history_path = self.config.get("memory", {}).get("history_path", "data/conversation_history.json")
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            logger.info(f"История взаимодействия сохранена в {history_path}")
    
    def process_input(self, user_input: str) -> str:
        """
        Обрабатывает запрос пользователя и возвращает ответ агента.
        
        Args:
            user_input: Текст запроса от пользователя.
            
        Returns:
            Ответ агента на запрос пользователя.
        """
        if not self.active:
            logger.warning("Попытка обработать запрос при неактивном агенте")
            return "Агент не активен. Пожалуйста, запустите агента с помощью метода start()."
        
        logger.info(f"Получен запрос: {user_input}")
        
        # Добавление запроса в историю
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": self._get_current_timestamp()
        })
        
        # Обработка запроса
        context = self.memory.get_relevant_context(user_input)
        reasoning = self.reasoner.analyze(user_input, context)
        
        # Планирование действий
        self.current_plan = self.planner.create_plan(user_input, reasoning, context)
        
        # Выполнение плана
        result = self.executor.execute_plan(
            self.current_plan,
            self.tool_manager,
            self.api_connector
        )
        
        # Формирование ответа
        response = self.reasoner.generate_response(result, user_input, context)
        
        # Добавление ответа в историю
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": self._get_current_timestamp()
        })
        
        # Обработка обратной связи
        self.feedback_handler.log_interaction(user_input, response, self.current_plan, result)
        
        # Обновление памяти
        self.memory.add_interaction(user_input, response)
        
        logger.info(f"Отправлен ответ длиной {len(response)} символов")
        return response
    
    def _get_current_timestamp(self) -> str:
        """Возвращает текущую временную метку в формате ISO."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_capabilities(self) -> List[str]:
        """
        Возвращает список возможностей агента.
        
        Returns:
            Список строк с описанием возможностей агента.
        """
        tools = self.tool_manager.list_available_tools()
        apis = self.api_connector.list_connected_apis()
        
        capabilities = [
            "Обработка естественного языка",
            "Планирование последовательности действий",
            "Рассуждение и анализ информации",
            "Долговременная память взаимодействия"
        ]
        
        # Добавляем информацию о типе LLM
        llm_type = self.config.get("llm", {}).get("type", "llama_cpp")
        if llm_type == "external":
            api_url = self.config.get("llm", {}).get("external_api", {}).get("url", "")
            capabilities.append(f"Использование внешнего LLM API: {api_url}")
        else:
            capabilities.append("Использование локальной модели llama.cpp")
        
        capabilities.extend([f"Инструмент: {tool}" for tool in tools])
        capabilities.extend([f"API соединение: {api}" for api in apis])
        
        return capabilities
    
    def reset(self) -> None:
        """Сбрасывает состояние агента, очищая историю разговора и текущий план."""
        logger.info("Сброс состояния агента")
        self.conversation_history = []
        self.current_plan = None
        self.memory.clear()


def main():
    """Точка входа для запуска агента из командной строки."""
    parser = argparse.ArgumentParser(description="GC-Forged Pylot Agent")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/agent_config.json",
        help="Путь к файлу конфигурации агента"
    )
    parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Запустить агента в интерактивном режиме"
    )
    parser.add_argument(
        "--use-external", 
        action="store_true",
        help="Использовать внешний LLM API вместо локального"
    )
    
    args = parser.parse_args()
    
    # Загружаем конфигурацию и модифицируем при необходимости
    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    if args.use_external:
        config["llm"]["type"] = "external"
        logger.info("Используем внешний LLM API")
    
    # Временно сохраняем модифицированную конфигурацию
    temp_config_path = "config/temp_agent_config.json"
    with open(temp_config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    # Создаем и запускаем агента с модифицированной конфигурацией
    agent = PylotAgent(config_path=temp_config_path)
    agent.start()
    
    try:
        if args.interactive:
            print("GC-Forged Pylot Agent запущен. Для выхода введите 'exit' или нажмите Ctrl+C.")
            print(f"Используется {'внешний API' if config['llm']['type'] == 'external' else 'локальная модель'}")
            while True:
                user_input = input("\nВы: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                response = agent.process_input(user_input)
                print(f"\nАгент: {response}")
    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания. Завершение работы...")
    finally:
        agent.stop()
        # Удаляем временный файл конфигурации
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        print("GC-Forged Pylot Agent остановлен.")


# --- Add this block for testing ---
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Attempting to instantiate PylotAgent with placeholders...")

    # Import necessary placeholders and core components
    from .planner import Planner
    from .executor import Executor
    from .memory import Memory
    from .reasoner import Reasoner
    from .llm_interface_adapter import AgentLLMInterface
    from .tool_manager import ToolManager
    from .feedback_handler import FeedbackHandler
    # You might need a dummy core LLM or the actual one if configured
    # For now, let's create a dummy core LLM for the adapter
    class DummyCoreLLM:
        def generate(self, prompt, **kwargs): return "dummy generation"
        def chat(self, messages, **kwargs): return "dummy chat"

    try:
        # Create placeholder instances
        dummy_core_llm = DummyCoreLLM()
        agent_llm_interface = AgentLLMInterface(core_llm=dummy_core_llm)
        memory = Memory()
        tool_manager = ToolManager()
        planner = Planner(llm_interface=agent_llm_interface)
        reasoner = Reasoner(llm_interface=agent_llm_interface)
        executor = Executor(tool_manager=tool_manager, llm_interface=agent_llm_interface)
        feedback_handler = FeedbackHandler()

        # Agent configuration (minimal example)
        agent_config = {
            "agent_name": "TestAgent",
            "description": "Agent using placeholder components",
            "max_iterations": 5
        }

        # Instantiate the agent
        agent = PylotAgent(
            config=agent_config,
            llm_interface=agent_llm_interface,
            memory=memory,
            planner=planner,
            reasoner=reasoner,
            executor=executor,
            tool_manager=tool_manager,
            feedback_handler=feedback_handler
        )

        logger.info(f"PylotAgent '{agent.agent_name}' instantiated successfully!")

        # Optional: Try calling a simple method like process_input
        # logger.info("Testing process_input...")
        # result = agent.process_input("What is the weather like?")
        # logger.info(f"process_input result: {result}")

    except ImportError as e:
        logger.error(f"Import error during instantiation: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error during agent instantiation or test: {e}", exc_info=True)