#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Planning System
===================================

Module for creating action plans based on request analysis.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import logging
from typing import Dict, List, Any, Optional, Union

from .llm_interface import LLMInterface
from .reasoning import Reasoner

logger = logging.getLogger(__name__)


class Plan:
    """Представление плана действий."""
    
    def __init__(self, steps: List[Dict[str, Any]], goal: str, context: Dict[str, Any] = None):
        """
        Инициализирует план действий.
        
        Args:
            steps: Список шагов плана
            goal: Цель плана
            context: Дополнительный контекст
        """
        self.steps = steps
        self.goal = goal
        self.context = context or {}
        self.current_step = 0
        
    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает следующий шаг плана.
        
        Returns:
            Следующий шаг или None, если план завершен
        """
        if self.is_completed():
            return None
        
        step = self.steps[self.current_step]
        return step
    
    def advance(self) -> bool:
        """
        Переходит к следующему шагу плана.
        
        Returns:
            True, если переход успешен, False, если план уже завершен
        """
        if self.is_completed():
            return False
        
        self.current_step += 1
        return True
    
    def is_completed(self) -> bool:
        """
        Проверяет, завершен ли план.
        
        Returns:
            True, если все шаги плана выполнены
        """
        return self.current_step >= len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует план в словарь.
        
        Returns:
            Словарь с данными плана
        """
        return {
            "goal": self.goal,
            "steps": self.steps,
            "current_step": self.current_step,
            "context": self.context,
            "total_steps": len(self.steps),
            "completed": self.is_completed()
        }


class Planner:
    """
    Класс для создания планов действий на основе анализа запросов.
    
    Использует языковую модель для генерации последовательности
    шагов, необходимых для выполнения запроса пользователя.
    """
    
    def __init__(self, llm: LLMInterface, reasoner: Reasoner, config: Dict[str, Any] = None):
        """
        Инициализирует систему планирования.
        
        Args:
            llm: Интерфейс языковой модели
            reasoner: Система рассуждения
            config: Конфигурация системы планирования
        """
        self.llm = llm
        self.reasoner = reasoner
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.max_steps = self.config.get("max_steps", 5)
        
        logger.info(f"Система планирования инициализирована (enabled={self.enabled})")
    
    def create_plan(self, user_input: str, analysis: Dict[str, Any], context: List[Dict[str, Any]] = None) -> Plan:
        """
        Создает план действий на основе запроса пользователя и его анализа.
        
        Args:
            user_input: Запрос пользователя
            analysis: Результат анализа запроса
            context: Контекст из истории взаимодействия
            
        Returns:
            План действий
        """
        if not self.enabled:
            # Если планирование отключено, возвращаем простой план с одним шагом
            return Plan(
                steps=[{
                    "type": "direct_response",
                    "description": "Прямой ответ на запрос",
                    "input": user_input,
                    "output_key": "response"
                }],
                goal=f"Ответить на запрос: {user_input}"
            )
        
        # Создание промпта для генерации плана
        prompt = self._create_plan_prompt(user_input, analysis, context)
        
        # Получение ответа от LLM
        response = self.llm.generate(prompt, temperature=0.4)
        
        # Обработка ответа
        steps = self._parse_plan_response(response.text)
        
        # Ограничение количества шагов
        if len(steps) > self.max_steps:
            logger.warning(f"План содержит слишком много шагов ({len(steps)}). Ограничиваем до {self.max_steps}.")
            steps = steps[:self.max_steps]
        
        return Plan(
            steps=steps,
            goal=f"Ответить на запрос: {user_input}",
            context={
                "user_input": user_input,
                "analysis": analysis
            }
        )
    
    def _create_plan_prompt(self, user_input: str, analysis: Dict[str, Any], context: List[Dict[str, Any]] = None) -> str:
        """
        Создает промпт для генерации плана.
        
        Args:
            user_input: Запрос пользователя
            analysis: Результат анализа запроса
            context: Контекст из истории взаимодействия
            
        Returns:
            Промпт для генерации плана
        """
        intent = analysis.get("intent", "")
        complexity = analysis.get("complexity", "medium")
        tools_needed = ", ".join(analysis.get("tools_needed", []))
        
        prompt = f"""Создай план действий для ответа на запрос пользователя.

Запрос пользователя: {user_input}

Анализ запроса:
- Намерение: {intent}
- Сложность: {complexity}
- Необходимые инструменты: {tools_needed}

Разработай пошаговый план действий для выполнения запроса. План должен быть разбит на логические шаги.
Для каждого шага укажи:
1. Тип шага (search_info, generate_code, analyze_data, direct_response и т.д.)
2. Описание шага
3. Входные данные для шага
4. Ключ для выходных данных

Формат плана:
STEP 1:
TYPE: [тип шага]
DESCRIPTION: [описание]
INPUT: [входные данные]
OUTPUT_KEY: [ключ для выходных данных]

STEP 2:
...

Ограничения:
- Максимум {self.max_steps} шагов
- Последний шаг должен формировать финальный ответ пользователю
"""
        return prompt
    
    def _parse_plan_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Обрабатывает ответ LLM и извлекает шаги плана.
        
        Args:
            response: Ответ от языковой модели
            
        Returns:
            Список шагов плана
        """
        steps = []
        current_step = {}
        current_property = None
        
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Новый шаг
            if line.lower().startswith("step"):
                # Сохраняем предыдущий шаг, если есть
                if current_step:
                    steps.append(current_step)
                current_step = {}
                current_property = None
                continue
            
            # Свойства шага
            if line.startswith("TYPE:"):
                current_step["type"] = line[len("TYPE:"):].strip()
                current_property = "type"
            elif line.startswith("DESCRIPTION:"):
                current_step["description"] = line[len("DESCRIPTION:"):].strip()
                current_property = "description"
            elif line.startswith("INPUT:"):
                current_step["input"] = line[len("INPUT:"):].strip()
                current_property = "input"
            elif line.startswith("OUTPUT_KEY:"):
                current_step["output_key"] = line[len("OUTPUT_KEY:"):].strip()
                current_property = "output_key"
            # Продолжение предыдущего свойства
            elif current_property:
                current_step[current_property] += " " + line
        
        # Добавляем последний шаг
        if current_step:
            steps.append(current_step)
        
        # Если план пустой, создаем default план
        if not steps:
            steps = [{
                "type": "direct_response",
                "description": "Прямой ответ на запрос",
                "input": "Исходный запрос пользователя",
                "output_key": "response"
            }]
        
        return steps