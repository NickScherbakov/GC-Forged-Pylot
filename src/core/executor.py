#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Система выполнения
=================================

Модуль для выполнения планов действий.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)


class Executor:
    """
    Класс для выполнения планов действий.
    
    Выполняет шаги плана, управляет результатами и обрабатывает ошибки.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует систему выполнения.
        
        Args:
            config: Конфигурация системы выполнения
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)  # Таймаут в секундах
        self.max_retries = self.config.get("max_retries", 2)  # Максимальное количество попыток
        
        # Обработчики для различных типов шагов
        self.handlers = {
            "direct_response": self._handle_direct_response,
            "search_info": self._handle_search_info,
            "generate_code": self._handle_generate_code,
            "analyze_data": self._handle_analyze_data
        }
        
        logger.info("Система выполнения инициализирована")
    
    def execute_plan(self, plan, tool_manager, api_connector) -> Dict[str, Any]:
        """
        Выполняет план действий.
        
        Args:
            plan: План действий для выполнения
            tool_manager: Менеджер инструментов
            api_connector: Коннектор API
            
        Returns:
            Результаты выполнения плана
        """
        logger.info(f"Начало выполнения плана: {plan.goal}")
        
        results = {
            "success": True,
            "steps_completed": 0,
            "outputs": {},
            "errors": [],
            "execution_time": 0
        }
        
        start_time = time.time()
        
        while not plan.is_completed():
            step = plan.get_next_step()
            
            if not step:
                break
                
            logger.info(f"Выполнение шага {plan.current_step + 1}: {step.get('description', 'Без описания')}")
            
            # Получение обработчика для типа шага
            step_type = step.get("type", "direct_response")
            handler = self.handlers.get(step_type, self._handle_unknown)
            
            # Выполнение шага с поддержкой повторных попыток
            step_success = False
            step_output = None
            step_error = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"Повторная попытка {attempt}/{self.max_retries}")
                    
                    # Выполнение шага с контекстом предыдущих результатов
                    step_output = handler(step, results["outputs"], tool_manager, api_connector)
                    step_success = True
                    break
                except Exception as e:
                    step_error = str(e)
                    logger.error(f"Ошибка при выполнении шага: {str(e)}")
                    time.sleep(1)  # Пауза перед повторной попыткой
            
            # Обработка результатов шага
            if step_success:
                output_key = step.get("output_key", f"step_{plan.current_step}")
                results["outputs"][output_key] = step_output
                results["steps_completed"] += 1
                plan.advance()
            else:
                results["success"] = False
                results["errors"].append({
                    "step": plan.current_step,
                    "description": step.get("description", ""),
                    "error": step_error
                })
                break
        
        results["execution_time"] = time.time() - start_time
        
        logger.info(f"План выполнен: успех={results['success']}, шагов выполнено={results['steps_completed']}")
        return results
    
    def _handle_direct_response(self, step, previous_outputs, tool_manager, api_connector) -> str:
        """Обрабатывает шаг прямого ответа."""
        # В простой реализации просто возвращаем входные данные
        return step.get("input", "")
    
    def _handle_search_info(self, step, previous_outputs, tool_manager, api_connector) -> Dict[str, Any]:
        """Обрабатывает шаг поиска информации."""
        query = step.get("input", "")
        
        # Проверяем, есть ли инструмент поиска
        if tool_manager.has_tool("web_search"):
            search_tool = tool_manager.get_tool("web_search")
            return search_tool.execute(query=query)
        
        # Если нет инструмента, возвращаем заглушку
        return {
            "query": query,
            "results": [],
            "message": "Инструмент поиска недоступен"
        }
    
    def _handle_generate_code(self, step, previous_outputs, tool_manager, api_connector) -> str:
        """Обрабатывает шаг генерации кода."""
        # Здесь можно добавить вызов специализированного инструмента для генерации кода
        # В простой реализации возвращаем заглушку
        return "# Здесь будет сгенерированный код\nprint('Hello, world!')"
    
    def _handle_analyze_data(self, step, previous_outputs, tool_manager, api_connector) -> Dict[str, Any]:
        """Обрабатывает шаг анализа данных."""
        # В простой реализации возвращаем заглушку
        return {
            "analysis_result": "Данные проанализированы",
            "summary": "Краткое описание результатов"
        }
    
    def _handle_unknown(self, step, previous_outputs, tool_manager, api_connector) -> str:
        """Обрабатывает неизвестный тип шага."""
        logger.warning(f"Неизвестный тип шага: {step.get('type')}")
        return f"Шаг типа '{step.get('type')}' не реализован"