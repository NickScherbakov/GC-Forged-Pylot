#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Feedback Handler
=======================================

Module for collecting and processing user feedback.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedbackHandler:
    """
    Класс для processing feedback от пользователя.
    
    Собирает информацию о взаимодействии пользователя с системой,
    сохраняет историю взаимодействий и предоставляет интерфейс
    для улучшения работы системы на основе feedback.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует обработчик feedback.
        
        Args:
            config: Конфигурация обработчика feedback
        """
        self.config = config or {}
        self.interactions = []  # История взаимодействий
        self.log_path = self.config.get("log_path", "logs/feedback.log")
        self.save_interactions = self.config.get("save_interactions", True)
        
        # Create директорию для логов, если не существует
        if self.save_interactions:
            log_dir = os.path.dirname(self.log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        
        logger.info("Обработчик feedback инициализирован")
    
    def log_interaction(self, user_input: str, assistant_output: str, plan: Any = None, execution_results: Dict[str, Any] = None) -> None:
        """
        Логирует взаимодействие с пользователем.
        
        Args:
            user_input: Запрос пользователя
            assistant_output: Ответ ассистента
            plan: План действий (опционально)
            execution_results: Результаты execution плана (опционально)
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Create запись interaction
        interaction = {
            "timestamp": timestamp,
            "user_input": user_input,
            "assistant_output": assistant_output
        }
        
        # Add информацию о плане, если доступна
        if plan:
            interaction["plan"] = {
                "goal": getattr(plan, "goal", ""),
                "steps_count": len(getattr(plan, "steps", [])),
                "current_step": getattr(plan, "current_step", 0)
            }
        
        # Add информацию о результатах execution, если доступна
        if execution_results:
            interaction["execution"] = {
                "success": execution_results.get("success", False),
                "steps_completed": execution_results.get("steps_completed", 0),
                "execution_time": execution_results.get("execution_time", 0),
                "errors": execution_results.get("errors", [])
            }
        
        # Сохраняем взаимодействие в истории
        self.interactions.append(interaction)
        
        # Записываем взаимодействие в лог, если включено
        if self.save_interactions:
            self._write_to_log(interaction)
    
    def _write_to_log(self, interaction: Dict[str, Any]) -> None:
        """
        Записывает взаимодействие в лог.
        
        Args:
            interaction: Данные interaction
        """
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(interaction, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Ошибка при записи в лог: {str(e)}")
    
    def add_feedback(self, interaction_id: str, rating: int, comment: str = "") -> bool:
        """
        Добавляет обратную связь для конкретного interaction.
        
        Args:
            interaction_id: Идентификатор interaction
            rating: Оценка (от 1 до 5)
            comment: Комментарий пользователя
            
        Returns:
            bool: True, если обратная связь успешно добавлена, иначе False
        """
        # Check корректность оценки
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            logger.error(f"Некорректная оценка: {rating}")
            return False
        
        # Ищем взаимодействие по ID
        for interaction in self.interactions:
            if interaction.get("id") == interaction_id:
                # Add обратную связь
                interaction["feedback"] = {
                    "rating": rating,
                    "comment": comment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Записываем обновленное взаимодействие в лог, если включено
                if self.save_interactions:
                    self._write_to_log(interaction)
                
                return True
        
        logger.warning(f"Взаимодействие с ID '{interaction_id}' не найдено")
        return False
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по feedback.
        
        Returns:
            Dict[str, Any]: Статистика по feedback
        """
        total_interactions = len(self.interactions)
        feedback_count = sum(1 for i in self.interactions if "feedback" in i)
        
        ratings = [i.get("feedback", {}).get("rating", 0) for i in self.interactions if "feedback" in i]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "total_interactions": total_interactions,
            "feedback_count": feedback_count,
            "feedback_percentage": (feedback_count / total_interactions * 100) if total_interactions > 0 else 0,
            "average_rating": avg_rating,
            "ratings_distribution": {
                "1": ratings.count(1),
                "2": ratings.count(2),
                "3": ratings.count(3),
                "4": ratings.count(4),
                "5": ratings.count(5)
            }
        }