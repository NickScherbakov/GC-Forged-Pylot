#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot Tasks
=====================

Module for defining and managing GC-Forged Pylot agent tasks.
Provides structure for creating, tracking, and executing complex tasks,
as well as their decomposition into subtasks.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import sys
import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from enum import Enum, auto

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PylotTasks")


class TaskStatus(Enum):
    """Статусы задачи агента."""
    PENDING = auto()      # Задача создана, но не начата
    IN_PROGRESS = auto()  # Задача выполняется
    COMPLETED = auto()    # Задача успешно выполнена
    FAILED = auto()       # Задача завершилась с ошибкой
    BLOCKED = auto()      # Выполнение задачи заблокировано
    CANCELLED = auto()    # Задача отменена


class TaskPriority(Enum):
    """Приоритеты задачи агента."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskType(Enum):
    """Типы задач агента."""
    RESPONSE = auto()     # Формирование ответа на запрос
    CODE = auto()         # Работа с кодом (анализ, генерация, рефакторинг)
    RESEARCH = auto()     # Исследование информации
    PLANNING = auto()     # Планирование действий
    EXECUTION = auto()    # Выполнение операций
    EVALUATION = auto()   # Оценка результатов
    INTEGRATION = auto()  # Интеграция с внешними системами


class Task:
    """
    Класс представляющий задачу агента Pylot.
    
    Задача - это структурированная единица работы, которую должен выполнить агент.
    Может содержать подзадачи, зависимости и метаданные для отслеживания прогресса.
    """
    
    def __init__(
        self,
        title: str,
        description: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.NORMAL,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Инициализирует новую задачу.
        
        Args:
            title: Краткое название задачи
            description: Подробное описание задачи
            task_type: Тип задачи
            priority: Приоритет задачи
            parent_id: ID родительской задачи (если это подзадача)
            metadata: Дополнительные метаданные задачи
        """
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.task_type = task_type
        self.priority = priority
        self.parent_id = parent_id
        self.metadata = metadata or {}
        
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.completed_at = None
        
        self.subtasks: List[str] = []  # ID подзадач
        self.dependencies: List[str] = []  # ID задач, от которых зависит эта задача
        
        self.progress = 0.0  # Прогресс execution от 0.0 до 1.0
        self.result = None  # Результат execution задачи
        self.error = None  # Информация об ошибке, если задача не выполнена
        
        logger.debug(f"Создана задача {self.id}: {self.title}")
    
    def add_subtask(self, subtask: 'Task') -> None:
        """
        Добавляет подзадачу.
        
        Args:
            subtask: Объект подзадачи
        """
        subtask.parent_id = self.id
        self.subtasks.append(subtask.id)
        self.update()
        logger.debug(f"К задаче {self.id} добавлена подзадача {subtask.id}")
    
    def add_dependency(self, dependency_id: str) -> None:
        """
        Добавляет зависимость от другой задачи.
        
        Args:
            dependency_id: ID задачи, от которой зависит эта задача
        """
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
            self.update()
            logger.debug(f"К задаче {self.id} добавлена зависимость {dependency_id}")
    
    def update_status(self, status: TaskStatus) -> None:
        """
        Обновляет статус задачи.
        
        Args:
            status: Новый статус задачи
        """
        old_status = self.status
        self.status = status
        
        if status == TaskStatus.COMPLETED:
            self.progress = 1.0
            self.completed_at = datetime.utcnow().isoformat()
        
        self.update()
        logger.info(f"Статус задачи {self.id} изменен с {old_status} на {status}")
    
    def update_progress(self, progress: float) -> None:
        """
        Обновляет прогресс execution задачи.
        
        Args:
            progress: Прогресс execution от 0.0 до 1.0
        """
        if 0.0 <= progress <= 1.0:
            self.progress = progress
            self.update()
            logger.debug(f"Прогресс задачи {self.id} обновлен до {progress:.2f}")
        else:
            logger.warning(f"Некорректное значение прогресса: {progress}")
    
    def set_result(self, result: Any) -> None:
        """
        Устанавливает результат execution задачи.
        
        Args:
            result: Результат execution задачи
        """
        self.result = result
        self.update()
        logger.debug(f"Для задачи {self.id} установлен результат")
    
    def set_error(self, error: str) -> None:
        """
        Устанавливает информацию об ошибке.
        
        Args:
            error: Описание ошибки
        """
        self.error = error
        self.update_status(TaskStatus.FAILED)
        logger.error(f"Задача {self.id} завершилась с ошибкой: {error}")
    
    def update(self) -> None:
        """Обновляет временную метку последнего изменения."""
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует задачу в словарь для сериализации.
        
        Returns:
            Словарь представляющий задачу
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.name,
            "priority": self.priority.name,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "status": self.status.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "subtasks": self.subtasks,
            "dependencies": self.dependencies,
            "progress": self.progress,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Создает задачу из словаря.
        
        Args:
            data: Словарь с данными задачи
        
        Returns:
            Объект задачи
        """
        task = cls(
            title=data["title"],
            description=data["description"],
            task_type=TaskType[data["task_type"]],
            priority=TaskPriority[data["priority"]],
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {})
        )
        
        task.id = data["id"]
        task.status = TaskStatus[data["status"]]
        task.created_at = data["created_at"]
        task.updated_at = data["updated_at"]
        task.completed_at = data.get("completed_at")
        task.subtasks = data.get("subtasks", [])
        task.dependencies = data.get("dependencies", [])
        task.progress = data.get("progress", 0.0)
        task.result = data.get("result")
        task.error = data.get("error")
        
        return task


class TaskManager:
    """
    Класс для management задачами агента Pylot.
    
    Выполняет создание, отслеживание и управление задачами,
    обеспечивает их сохранение и загрузку.
    """
    
    def __init__(self, storage_path: str = "data/tasks.json"):
        """
        Инициализирует менеджер задач.
        
        Args:
            storage_path: Путь к файлу для хранения задач
        """
        self.storage_path = storage_path
        self.tasks: Dict[str, Task] = {}
        self.load_tasks()
    
    def create_task(
        self,
        title: str,
        description: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.NORMAL,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Task:
        """
        Создает новую задачу.
        
        Args:
            title: Краткое название задачи
            description: Подробное описание задачи
            task_type: Тип задачи
            priority: Приоритет задачи
            parent_id: ID родительской задачи (если это подзадача)
            metadata: Дополнительные метаданные задачи
        
        Returns:
            Созданная задача
        """
        task = Task(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            parent_id=parent_id,
            metadata=metadata
        )
        
        self.tasks[task.id] = task
        
        if parent_id and parent_id in self.tasks:
            parent = self.tasks[parent_id]
            parent.add_subtask(task)
        
        self.save_tasks()
        logger.info(f"Создана новая задача: {task.id} - {task.title}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Возвращает задачу по ID.
        
        Args:
            task_id: ID задачи
        
        Returns:
            Объект задачи или None, если задача не найдена
        """
        return self.tasks.get(task_id)
    
    def update_task(self, task: Task) -> None:
        """
        Обновляет задачу в хранилище.
        
        Args:
            task: Обновленная задача
        """
        if task.id in self.tasks:
            self.tasks[task.id] = task
            self.save_tasks()
            logger.debug(f"Задача {task.id} обновлена")
    
    def delete_task(self, task_id: str) -> bool:
        """
        Удаляет задачу по ID.
        
        Args:
            task_id: ID задачи
        
        Returns:
            True при успешном удалении, иначе False
        """
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            
            # Удаляем связи с этой задачей
            for other_task in self.tasks.values():
                if task_id in other_task.dependencies:
                    other_task.dependencies.remove(task_id)
                if task_id in other_task.subtasks:
                    other_task.subtasks.remove(task_id)
            
            # Если это родительская задача, удаляем также все подзадачи
            if task and task.subtasks:
                for subtask_id in list(task.subtasks):
                    self.delete_task(subtask_id)
            
            self.save_tasks()
            logger.info(f"Задача {task_id} удалена")
            return True
        return False
    
    def list_tasks(
        self, 
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        priority: Optional[TaskPriority] = None,
        parent_id: Optional[str] = None
    ) -> List[Task]:
        """
        Возвращает список задач с фильтрацией.
        
        Args:
            status: Фильтр по статусу
            task_type: Фильтр по типу задачи
            priority: Фильтр по приоритету
            parent_id: Фильтр по ID родительской задачи
        
        Returns:
            Список задач, соответствующих фильтрам
        """
        filtered_tasks = self.tasks.values()
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]
        
        if task_type:
            filtered_tasks = [t for t in filtered_tasks if t.task_type == task_type]
        
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
        
        if parent_id is not None:
            filtered_tasks = [t for t in filtered_tasks if t.parent_id == parent_id]
        
        # Сортировка по приоритету и времени создания
        return sorted(
            filtered_tasks,
            key=lambda t: (
                -t.priority.value,  # Сначала высокоприоритетные
                t.created_at  # Затем по времени создания
            )
        )
    
    def get_next_task(self) -> Optional[Task]:
        """
        Возвращает следующую задачу для execution.
        
        Returns:
            Задача с наивысшим приоритетом, готовая к выполнению,
            или None, если таких задач нет
        """
        # Получаем задачи со статусом PENDING
        pending_tasks = self.list_tasks(status=TaskStatus.PENDING)
        
        # Фильтруем задачи, у которых выполнены все зависимости
        ready_tasks = []
        for task in pending_tasks:
            dependencies_met = True
            for dep_id in task.dependencies:
                dep_task = self.get_task(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_tasks.append(task)
        
        # Возвращаем задачу с наивысшим приоритетом
        if ready_tasks:
            # Сортировка уже встроена в list_tasks, поэтому берем первую задачу
            return ready_tasks[0]
        
        return None
    
    def calculate_task_tree_progress(self, root_task_id: str) -> float:
        """
        Рассчитывает общий прогресс execution задачи с подзадачами.
        
        Args:
            root_task_id: ID корневой задачи
        
        Returns:
            Процент execution от 0.0 до 1.0
        """
        root_task = self.get_task(root_task_id)
        if not root_task:
            return 0.0
        
        # Если нет подзадач, возвращаем прогресс самой задачи
        if not root_task.subtasks:
            return root_task.progress
        
        # Суммируем прогресс подзадач
        total_weight = len(root_task.subtasks) + 1  # +1 для самой задачи
        total_progress = root_task.progress  # Прогресс самой задачи
        
        for subtask_id in root_task.subtasks:
            subtask = self.get_task(subtask_id)
            if subtask:
                # Рекурсивно вычисляем прогресс для подзадач
                subtask_progress = self.calculate_task_tree_progress(subtask_id)
                total_progress += subtask_progress
        
        return total_progress / total_weight
    
    def save_tasks(self) -> None:
        """Сохраняет задачи в файл."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        tasks_dict = {
            task_id: task.to_dict() for task_id, task in self.tasks.items()
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(tasks_dict, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"Задачи сохранены в {self.storage_path}")
    
    def load_tasks(self) -> None:
        """Загружает задачи из файла."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    tasks_dict = json.load(f)
                
                self.tasks = {
                    task_id: Task.from_dict(task_data)
                    for task_id, task_data in tasks_dict.items()
                }
                
                logger.info(f"Загружено {len(self.tasks)} задач из {self.storage_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки задач: {str(e)}")
                self.tasks = {}
        else:
            logger.info(f"Файл задач {self.storage_path} не найден, создаем новый")
            self.tasks = {}


class ContinuousTasks:
    """
    Класс для management непрерывным выполнением задач.
    
    Обеспечивает создание итераций execution задач агента,
    отслеживание последовательных задач и их взаимосвязей.
    """
    
    def __init__(self, task_manager: TaskManager):
        """
        Инициализирует менеджер непрерывных задач.
        
        Args:
            task_manager: Менеджер задач
        """
        self.task_manager = task_manager
        self.current_iteration = 0
        self.current_task_id = None
        self.completed_iterations = []
    
    def start_iteration(self, query: str) -> str:
        """
        Начинает новую итерацию processing запроса.
        
        Args:
            query: Текст запроса пользователя
        
        Returns:
            ID созданной задачи
        """
        self.current_iteration += 1
        
        # Create корневую задачу для итерации
        task = self.task_manager.create_task(
            title=f"Итерация #{self.current_iteration}",
            description=f"Обработка запроса: {query}",
            task_type=TaskType.RESPONSE,
            priority=TaskPriority.NORMAL,
            metadata={"query": query, "iteration": self.current_iteration}
        )
        
        self.current_task_id = task.id
        logger.info(f"Начата итерация #{self.current_iteration}, задача {task.id}")
        
        # Create стандартные подзадачи для processing запроса
        self._create_standard_subtasks(task.id, query)
        
        return task.id
    
    def _create_standard_subtasks(self, parent_id: str, query: str) -> None:
        """
        Создает стандартные подзадачи для processing запроса.
        
        Args:
            parent_id: ID родительской задачи
            query: Текст запроса пользователя
        """
        # Create подзадачу для planning
        planning_task = self.task_manager.create_task(
            title="Планирование",
            description="Анализ запроса и планирование действий",
            task_type=TaskType.PLANNING,
            parent_id=parent_id
        )
        
        # Create подзадачу для исполнения
        execution_task = self.task_manager.create_task(
            title="Исполнение",
            description="Выполнение запланированных действий",
            task_type=TaskType.EXECUTION,
            parent_id=parent_id
        )
        # Зависит от planning
        execution_task.add_dependency(planning_task.id)
        
        # Create подзадачу для оценки
        evaluation_task = self.task_manager.create_task(
            title="Оценка",
            description="Оценка результатов execution",
            task_type=TaskType.EVALUATION,
            parent_id=parent_id
        )
        # Зависит от исполнения
        evaluation_task.add_dependency(execution_task.id)
        
        # Update таски
        self.task_manager.update_task(execution_task)
        self.task_manager.update_task(evaluation_task)
    
    def complete_iteration(self, result: Any = None) -> None:
        """
        Завершает текущую итерацию.
        
        Args:
            result: Результат execution итерации
        """
        if self.current_task_id:
            task = self.task_manager.get_task(self.current_task_id)
            if task:
                task.update_status(TaskStatus.COMPLETED)
                task.set_result(result)
                self.task_manager.update_task(task)
                
                self.completed_iterations.append({
                    "iteration": self.current_iteration,
                    "task_id": self.current_task_id,
                    "result": result
                })
                
                logger.info(f"Завершена итерация #{self.current_iteration}, задача {self.current_task_id}")
            
            self.current_task_id = None
    
    def continue_iteration(self, query: str = "Продолжить итерацию") -> str:
        """
        Продолжает текущую итерацию с новым запросом.
        
        Args:
            query: Текст запроса для продолжения
        
        Returns:
            ID созданной задачи
        """
        if not self.current_task_id:
            return self.start_iteration(query)
        
        # Create задачу продолжения как подзадачу текущей итерации
        task = self.task_manager.create_task(
            title=f"Продолжение",
            description=f"Продолжение запроса: {query}",
            task_type=TaskType.RESPONSE,
            priority=TaskPriority.NORMAL,
            parent_id=self.current_task_id,
            metadata={"query": query, "iteration": self.current_iteration, "continuation": True}
        )
        
        logger.info(f"Создано продолжение для итерации #{self.current_iteration}, задача {task.id}")
        return task.id
    
    def get_iteration_history(self) -> List[Dict[str, Any]]:
        """
        Возвращает историю итераций.
        
        Returns:
            Список итераций с результатами
        """
        return self.completed_iterations
    
    def get_current_task_progress(self) -> float:
        """
        Возвращает прогресс текущей задачи.
        
        Returns:
            Процент execution от 0.0 до 1.0
        """
        if not self.current_task_id:
            return 0.0
        
        return self.task_manager.calculate_task_tree_progress(self.current_task_id)