#!/usr/bin/env python
"""
Скрипт запуска GC-Forged-Pylot в автономном режиме с самосовершенствованием.
Принимает задачу в виде параметра и запускает автономный цикл самообучения.
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pylot_agent.log')
    ]
)

logger = logging.getLogger("run_autonomous")

# Добавляем проект в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import load_config
from src.core.hardware_optimizer import HardwareOptimizer
from src.core.llm_interface import create_llm_interface
from src.core.memory import Memory
from src.core.executor import Executor
from src.core.reasoning import Reasoning
from src.core.planner import Planner
from src.bridge.feedback_handler import FeedbackHandler
from src.self_improvement import SelfImprovement


def initialize_system() -> tuple:
    """Инициализирует все необходимые компоненты системы."""
    logger.info("Инициализация системы GC-Forged-Pylot...")
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Оптимизируем параметры под текущее оборудование
    optimizer = HardwareOptimizer()
    optimizer._update_hardware_profile()
    
    # Инициализируем LLM
    llm = create_llm_interface()
    
    # Инициализируем базовые компоненты
    memory = Memory()
    executor = Executor(llm)
    reasoning = Reasoning(llm)
    planner = Planner(llm, reasoning)
    
    # Инициализируем обработчик обратной связи
    feedback_handler = FeedbackHandler(config.get("notification_channels", {}))
    
    # Инициализируем модуль самосовершенствования
    self_improvement = SelfImprovement(
        llm=llm, 
        memory=memory, 
        executor=executor, 
        reasoning=reasoning, 
        planner=planner,
        feedback_handler=feedback_handler
    )
    
    return config, self_improvement, feedback_handler


def main():
    parser = argparse.ArgumentParser(
        description="Запуск GC-Forged-Pylot в автономном режиме"
    )
    parser.add_argument(
        "task", 
        type=str,
        help="Задача для автономного выполнения"
    )
    parser.add_argument(
        "--notify", 
        type=str, 
        choices=["log", "email", "telegram", "all"], 
        default="log",
        help="Метод уведомления о завершении"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Запустить в режиме непрерывного самосовершенствования"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Максимальное количество циклов улучшения"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Порог уверенности для завершения (0-1)"
    )
    
    args = parser.parse_args()
    
    # Инициализируем систему
    config, self_improvement, feedback_handler = initialize_system()
    
    # Устанавливаем пользовательский порог уверенности
    self_improvement.confidence_threshold = args.threshold
    
    # Запускаем систему в выбранном режиме
    if args.continuous:
        logger.info(f"Запуск в режиме непрерывного самосовершенствования с задачей: {args.task[:100]}")
        self_improvement.continuous_improvement_daemon(
            initial_task=args.task,
            feedback_poll_interval=config.get("feedback_poll_interval", 3600),
            max_autonomous_cycles=10
        )
    else:
        logger.info(f"Запуск в режиме одиночной задачи с циклами улучшения: {args.task[:100]}")
        result = self_improvement.execute_task_with_improvement(
            task_description=args.task,
            max_improvement_cycles=args.cycles,
            notify_on_completion=True
        )
        
        # Выводим результаты
        print("\n" + "="*50)
        print(f"Задача выполнена с уверенностью: {result['confidence']:.2f}")
        print(f"Пороговое значение: {self_improvement.confidence_threshold} | " +
              f"{'✅ Превышено' if result['threshold_met'] else '❌ Не достигнуто'}")
        print(f"Циклов улучшения: {result['cycles_completed']}")
        print("="*50)
        print("\nРезультат:")
        print(result['result'])
        print("="*50)
        
        # Отправляем уведомление о завершении
        if args.notify != "log":
            channels = []
            if args.notify == "all":
                channels = list(config.get("notification_channels", {}).keys())
            else:
                channels = [args.notify]
                
            for channel in channels:
                self_improvement.send_notification(
                    message=f"Задача завершена с уверенностью {result['confidence']:.2f}.",
                    channel=channel,
                    metadata={"task": args.task, "result_summary": str(result['result'])[:200]}
                )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())