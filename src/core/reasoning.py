#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Reasoning System
==================================

Module for analyzing user requests and formulating responses.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import logging
from typing import Dict, List, Any, Optional, Union

from .llm_interface import LLMInterface

logger = logging.getLogger(__name__)


class Reasoner:
    """
    Класс для анализа пользовательских запросов и формирования ответов.
    
    Основан на языковой модели, выполняет анализ запросов, формирует
    reasoning и генерирует ответы.
    """
    
    def __init__(self, llm: LLMInterface, config: Dict[str, Any] = None):
        """
        Инициализирует систему reasoning.
        
        Args:
            llm: Интерфейс языковой модели
            config: Конфигурация системы reasoning
        """
        self.llm = llm
        self.config = config or {}
        self.chain_of_thought = self.config.get("chain_of_thought", True)
        self.verbosity = self.config.get("verbosity", "medium")
        
        logger.info("Система reasoning инициализирована")
    
    def analyze(self, user_input: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Анализирует пользовательский запрос и возвращает результаты анализа.
        
        Args:
            user_input: Запрос пользователя
            context: Контекст из истории interaction
            
        Returns:
            Результаты анализа запроса
        """
        logger.info(f"Анализ запроса: {user_input[:50]}...")
        
        # Формирование промпта для анализа
        if self.chain_of_thought:
            prompt = self._create_analysis_prompt(user_input, context)
            
            # Получение ответа от LLM
            response = self.llm.generate(prompt, temperature=0.5)
            
            # Обработка результата
            analysis = self._parse_analysis_response(response.text)
        else:
            # Упрощенный анализ без цепочки рассуждений
            analysis = {
                "intent": self._detect_simple_intent(user_input),
                "entities": [],
                "complexity": "medium",
                "tools_needed": []
            }
        
        logger.debug(f"Результат анализа: {analysis}")
        return analysis
    
    def _create_analysis_prompt(self, user_input: str, context: List[Dict[str, Any]] = None) -> str:
        """
        Создает промпт для анализа запроса.
        
        Args:
            user_input: Запрос пользователя
            context: Контекст из истории interaction
            
        Returns:
            Промпт для системы reasoning
        """
        context_str = ""
        if context and len(context) > 0:
            recent_context = context[-3:]  # Берем последние 3 записи из контекста
            context_str = "Предыдущий контекст:\n"
            for item in recent_context:
                context_str += f"Пользователь: {item.get('user_input', '')}\n"
                context_str += f"Ассистент: {item.get('assistant_output', '')}\n"
        
        prompt = f"""Проанализируй следующий запрос пользователя и дай структурированный ответ.

{context_str}

Запрос пользователя: {user_input}

Выполни следующие шаги:
1. Определи основное намерение пользователя
2. Определи ключевые сущности в запросе
3. Оцени сложность запроса (низкая, средняя, высокая)
4. Определи, какие инструменты могут понадобиться для ответа
5. Определи, нужны ли дополнительные данные для полного ответа

Сформируй ответ в следующем формате:
INTENT: [намерение]
ENTITIES: [сущность1, сущность2, ...]
COMPLEXITY: [сложность]
TOOLS_NEEDED: [инструмент1, инструмент2, ...]
ADDITIONAL_DATA_NEEDED: [да/нет]
REASONING: [твои reasoning]

"""
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """
        Обрабатывает ответ LLM и извлекает структурированную информацию.
        
        Args:
            response: Ответ от языковой модели
            
        Returns:
            Структурированный результат анализа
        """
        lines = response.strip().split("\n")
        analysis = {
            "intent": "",
            "entities": [],
            "complexity": "medium",
            "tools_needed": [],
            "additional_data_needed": False,
            "reasoning": ""
        }
        
        current_section = None
        reasoning_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("INTENT:"):
                analysis["intent"] = line[len("INTENT:"):].strip()
                current_section = "intent"
            elif line.startswith("ENTITIES:"):
                entities_str = line[len("ENTITIES:"):].strip()
                if entities_str:
                    analysis["entities"] = [e.strip() for e in entities_str.replace("[", "").replace("]", "").split(",")]
                current_section = "entities"
            elif line.startswith("COMPLEXITY:"):
                analysis["complexity"] = line[len("COMPLEXITY:"):].strip().lower()
                current_section = "complexity"
            elif line.startswith("TOOLS_NEEDED:"):
                tools_str = line[len("TOOLS_NEEDED:"):].strip()
                if tools_str and tools_str.lower() not in ["none", "[]"]:
                    analysis["tools_needed"] = [t.strip() for t in tools_str.replace("[", "").replace("]", "").split(",")]
                current_section = "tools_needed"
            elif line.startswith("ADDITIONAL_DATA_NEEDED:"):
                analysis["additional_data_needed"] = line[len("ADDITIONAL_DATA_NEEDED:"):].strip().lower() == "да"
                current_section = "additional_data_needed"
            elif line.startswith("REASONING:"):
                current_section = "reasoning"
            elif current_section == "reasoning":
                reasoning_lines.append(line)
        
        if reasoning_lines:
            analysis["reasoning"] = "\n".join(reasoning_lines)
        
        return analysis
    
    def _detect_simple_intent(self, user_input: str) -> str:
        """
        Простой детектор намерения пользователя.
        
        Args:
            user_input: Запрос пользователя
            
        Returns:
            Предполагаемое намерение пользователя
        """
        user_input = user_input.lower()
        
        if any(word in user_input for word in ["привет", "здравствуй", "добрый день", "hello", "hi"]):
            return "greeting"
        elif any(word in user_input for word in ["пока", "до свидания", "увидимся", "bye", "exit", "quit"]):
            return "farewell"
        elif "?" in user_input:
            return "question"
        elif any(word in user_input for word in ["помоги", "помощь", "help"]):
            return "help_request"
        else:
            return "statement"
    
    def generate_response(self, analysis_result: Dict[str, Any], user_input: str, context: List[Dict[str, Any]] = None) -> str:
        """
        Генерирует ответ на основе результатов анализа.
        
        Args:
            analysis_result: Результаты анализа запроса
            user_input: Запрос пользователя
            context: Контекст из истории interaction
            
        Returns:
            Текст ответа
        """
        # Формирование промпта для генерации ответа
        prompt = self._create_response_prompt(analysis_result, user_input, context)
        
        # Получение ответа от LLM
        response = self.llm.generate(prompt, temperature=0.7)
        
        return response.text
    
    def _create_response_prompt(self, analysis_result: Dict[str, Any], user_input: str, context: List[Dict[str, Any]] = None) -> str:
        """
        Создает промпт для генерации ответа.
        
        Args:
            analysis_result: Результаты анализа запроса
            user_input: Запрос пользователя
            context: Контекст из истории interaction
            
        Returns:
            Промпт для генерации ответа
        """
        context_str = ""
        if context and len(context) > 0:
            recent_context = context[-3:]  # Берем последние 3 записи из контекста
            context_str = "Предыдущий контекст:\n"
            for item in recent_context:
                context_str += f"Пользователь: {item.get('user_input', '')}\n"
                context_str += f"Ассистент: {item.get('assistant_output', '')}\n"
        
        intent = analysis_result.get("intent", "")
        entities = ", ".join(analysis_result.get("entities", []))
        complexity = analysis_result.get("complexity", "medium")
        reasoning = analysis_result.get("reasoning", "")
        
        prompt = f"""Сгенерируй ответ на запрос пользователя.

{context_str}

Запрос пользователя: {user_input}

Анализ запроса:
- Намерение: {intent}
- Сущности: {entities}
- Сложность: {complexity}
{reasoning if reasoning else ''}

Сформируй четкий и информативный ответ на запрос пользователя, исходя из анализа и доступной информации. 
Ответ должен быть полезным, лаконичным и дружелюбным.

"""
        return prompt