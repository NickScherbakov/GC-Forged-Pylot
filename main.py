#!/usr/bin/env python3
"""
GC-Forged-Pylot - Точка входа в приложение
Запускает локальный LLM сервер на базе llama.cpp с интеграцией GitHub Copilot

Автор: GC-Forged-Pylot Team
"""
import os
import sys
import argparse
import logging
import signal
import time
from pathlib import Path

# Добавляем src в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from core import LlamaServer, load_config
from core.api import LlamaAPI
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("gc-forged-pylot")

def parse_args():
    """Обработка аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="GC-Forged-Pylot - Локальный LLM сервер с интеграцией GitHub Copilot"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=os.environ.get("GC_MODEL_PATH", ""),
        help="Путь к файлу модели .gguf (или установите переменную окружения GC_MODEL_PATH)"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "config.json"),
        help="Путь к файлу конфигурации (по умолчанию: ./config.json)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Хост для API (по умолчанию: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Порт для API (по умолчанию: 8080)"
    )
    
    parser.add_argument(
        "--threads", "-t",
        type=int,
        default=0,  # 0 означает автоопределение
        help="Количество потоков CPU (по умолчанию: автоопределение)"
    )
    
    parser.add_argument(
        "--no-gpu",
        action="store_true",
        help="Отключить использование GPU"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Включить подробное логирование"
    )
    
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Запустить только серверную часть без API"
    )
    
    return parser.parse_args()


def setup_config(args):
    """Настройка конфигурации на основе аргументов."""
    # Загрузка или создание конфигурации
    config_path = args.config if os.path.exists(args.config) else None
    config = load_config(config_path)
    
    # Обновление конфигурации на основе аргументов командной строки
    if args.model:
        config.model_path = args.model
    
    if args.threads > 0:
        config.threads = args.threads
    
    if args.no_gpu:
        config.use_gpu = False
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        config.verbose = True
    
    config.host = args.host
    config.port = args.port
    
    # Проверка наличия модели
    if not config.model_path:
        logger.error("Путь к модели не указан. Используйте --model или установите GC_MODEL_PATH.")
        sys.exit(1)
    
    if not os.path.exists(config.model_path):
        logger.error(f"Модель не найдена: {config.model_path}")
        sys.exit(1)
    
    return config


def setup_signal_handlers(server):
    """Настройка обработчиков сигналов для корректного завершения."""
    def handle_signal(sig, frame):
        logger.info(f"Получен сигнал {sig}, завершение работы...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def display_server_info(config):
    """Отображает информацию о запущенном сервере."""
    model_name = os.path.basename(config.model_path)
    
    logger.info("=" * 60)
    logger.info(f" GC-Forged-Pylot запущен!")
    logger.info("-" * 60)
    logger.info(f" Модель: {model_name}")
    logger.info(f" API доступно по адресу: http://{config.host}:{config.port}")
    logger.info(f" Количество потоков: {config.threads}")
    logger.info(f" Использование GPU: {'Да' if config.use_gpu else 'Нет'}")
    logger.info("=" * 60)
    logger.info(" Нажмите Ctrl+C для завершения")


def main():
    """Основная функция запуска приложения."""
    # Вывод заголовка
    logger.info("=" * 60)
    logger.info(" GC-Forged-Pylot - Автономная система программирования 24/7")
    logger.info("=" * 60)
    
    args = parse_args()
    config = setup_config(args)
    
    # Инициализация сервера Llama
    server = LlamaServer(model_path=config.model_path, config=config)
    setup_signal_handlers(server)
    
    # Запуск сервера
    if args.server_only:
        # Режим только сервера (без API)
        if not server.start():
            logger.error("Не удалось запустить сервер")
            sys.exit(1)
        
        display_server_info(config)
        
        # Держим процесс активным
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Завершение работы...")
            server.stop()
    else:
        # Режим API + сервер
        if not server.start():
            logger.error("Не удалось запустить сервер")
            sys.exit(1)
        
        # Инициализация FastAPI приложения
        api = LlamaAPI(server)
        
        display_server_info(config)
        
        # Запуск Uvicorn (API)
        try:
            uvicorn.run(api.app, host=config.host, port=config.port)
        finally:
            logger.info("Остановка сервера...")
            server.stop()


if __name__ == "__main__":
    main()