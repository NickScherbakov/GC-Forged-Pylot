#!/usr/bin/env python
"""
Скрипт для оптимизации llama.cpp под конкретное оборудование.
Анализирует аппаратное обеспечение, компилирует оптимизированную версию сервера
и создает профиль оптимальных параметров запуска.
"""
import os
import sys
import argparse
import logging
import time
from pathlib import Path

# Добавляем проект в путь импорта
sys.path.insert(0, str(Path(__file__).parent))

from src.core.hardware_optimizer import HardwareOptimizer
from src.core.config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('optimize_llama.log')
    ]
)

logger = logging.getLogger("optimize_llama")


def main():
    parser = argparse.ArgumentParser(
        description="Оптимизация llama.cpp под конкретное оборудование"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        help="Путь к файлу модели для бенчмаркинга"
    )
    parser.add_argument(
        "--compile", 
        action="store_true", 
        help="Скомпилировать оптимизированную версию сервера"
    )
    parser.add_argument(
        "--benchmark", 
        action="store_true", 
        help="Запустить бенчмарк"
    )
    parser.add_argument(
        "--llama-cpp", 
        type=str, 
        help="Путь к исходникам llama.cpp"
    )
    parser.add_argument(
        "--prompt", 
        type=str, 
        help="Текст для бенчмарка", 
        default="Объясни теорию относительности простыми словами."
    )
    parser.add_argument(
        "--iterations", 
        type=int, 
        help="Количество итераций бенчмарка", 
        default=3
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Принудительно запустить оптимизацию, даже если профиль актуален"
    )
    parser.add_argument(
        "--skip-compilation", 
        action="store_true", 
        help="Пропустить этап компиляции сервера (для систем без инструментов разработки)"
    )
    
    args = parser.parse_args()
    
    # Инициализируем оптимизатор
    optimizer = HardwareOptimizer()
    
    if args.force:
        # Принудительно создаем новый профиль при запуске с --force
        logger.info("Принудительное создание нового профиля оптимизации")
        optimizer._create_new_profile()
    
    # Определяем путь к модели
    model_path = args.model
    if not model_path:
        # Если путь не указан, пробуем загрузить из конфига
        config = load_config()
        model_path = config.model_path
        
        if not os.path.exists(model_path):
            logger.warning(f"Модель не найдена по пути {model_path}")
            model_path = None
    
    if args.compile or (args.model is None and not args.benchmark):
        # Компилируем оптимизированную версию сервера
        if args.skip_compilation:
            logger.info("Этап компиляции пропущен (--skip-compilation)")
        else:
            logger.info("Запуск компиляции оптимизированного сервера")
            start_time = time.time()
            success = optimizer.compile_optimized_server(args.llama_cpp)
            
            if success:
                logger.info(f"Сервер успешно скомпилирован за {time.time() - start_time:.1f} сек")
            else:
                logger.error("Не удалось скомпилировать сервер")
                return 1
    
    if args.benchmark and model_path:
        # Запускаем бенчмарк
        logger.info(f"Запуск бенчмарка на модели: {model_path}")
        start_time = time.time()
        
        if args.skip_compilation:
            # Используем имитацию бенчмарка, если сервер недоступен
            logger.info("Используем имитационный бенчмарк (--skip-compilation)")
            result = optimizer.run_mock_benchmark(
                model_path=model_path,
                prompt=args.prompt,
                iterations=args.iterations
            )
        else:
            # Используем реальный бенчмарк
            result = optimizer.run_benchmark(
                model_path=model_path,
                prompt=args.prompt,
                iterations=args.iterations
            )
        
        logger.info(f"Бенчмарк завершен за {time.time() - start_time:.1f} сек")
        logger.info(f"Результаты: {result.tokens_per_second:.2f} токенов/сек, "
                  f"латентность: {result.latency_ms:.2f} мс")
    else:
        # Просто обновляем профиль оборудования и параметры
        if model_path:
            # Полная оптимизация с бенчмаркингом
            logger.info("Запуск полной оптимизации с бенчмаркингом")
            results = optimizer.run_optimization(model_path)
            logger.info(f"Оптимизация завершена. Оптимальные параметры запуска:")
            logger.info(f"- Потоки: {results['runtime_parameters']['n_threads']}")
            logger.info(f"- Контекст: {results['runtime_parameters']['n_ctx']}")
            logger.info(f"- Размер батча: {results['runtime_parameters']['batch_size']}")
            logger.info(f"- GPU слои: {results['runtime_parameters']['n_gpu_layers']}")
        else:
            # Оптимизация без бенчмаркинга
            logger.info("Запуск оптимизации без бенчмаркинга (не указан путь к модели)")
            optimizer._update_hardware_profile()
            compilation_flags = optimizer.optimize_compilation_flags()
            runtime_params = optimizer.optimize_runtime_parameters()
            
            logger.info("Оптимизация завершена. Предполагаемые оптимальные параметры:")
            logger.info(f"- Потоки: {runtime_params.n_threads}")
            logger.info(f"- Контекст: {runtime_params.n_ctx}")
            logger.info(f"- Размер батча: {runtime_params.batch_size}")
            logger.info(f"- GPU слои: {runtime_params.n_gpu_layers}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())