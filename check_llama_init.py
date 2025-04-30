import os
import logging
import sys # Import sys for exit
from pathlib import Path

# Настройка логирования для вывода информации
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

# Создадим фиктивный файл, если его нет
dummy_model_filename = "dummy_model_check.gguf"
logger.info(f"Checking for dummy model file: {dummy_model_filename}")
if not os.path.exists(dummy_model_filename):
    logger.info(f"Creating dummy model file: {dummy_model_filename}")
    try:
        with open(dummy_model_filename, 'w') as f:
            f.write("dummy check file for llama_cpp initialization test")
        logger.info("Dummy file created successfully.")
    except Exception as e:
        logger.error(f"Failed to create dummy file: {e}", exc_info=True)
        logger.error("Exiting due to dummy file creation failure.")
        sys.exit(1) # Use sys.exit for cleaner exit
else:
    logger.info(f"Dummy model file '{dummy_model_filename}' already exists.")

logger.info("Attempting to import Llama from llama_cpp...")
try:
    from llama_cpp import Llama
    logger.info("Llama imported successfully.")

    logger.info(f"Attempting to initialize Llama with dummy model path: {dummy_model_filename}")
    initialization_successful = False
    try:
        # Попытка инициализации с минимальными параметрами и фиктивным путем
        llm = Llama(
            model_path=dummy_model_filename,
            n_ctx=512,       # Минимальный контекст
            n_gpu_layers=0, # Без использования GPU для этого теста
            verbose=True     # Включим подробный вывод от llama_cpp
        )
        # Если инициализация не вызвала исключение, считаем ее успешной на этом этапе
        logger.info("Llama initialized successfully (using dummy model path).")
        logger.info("Note: This only checks library loading and basic initialization, not model validity.")
        initialization_successful = True

    except Exception as e:
        logger.error(f"Error during Llama initialization: {e}", exc_info=True)
        logger.error("This might indicate issues with llama-cpp-python installation, dependencies (like compilers or BLAS libraries), or basic library loading.")

except ImportError as e:
    logger.error(f"Failed to import Llama from llama_cpp: {e}", exc_info=True)
    logger.error("Please ensure 'llama-cpp-python' is installed correctly in the Python environment.")
except Exception as e:
    logger.error(f"An unexpected error occurred during import phase: {e}", exc_info=True)

# Проверка загрузки модели с использованием LlamaCppModel
logger.info("Checking model loading with LlamaCppModel...")
try:
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from src.core.llm_llama_cpp import LlamaCppModel

    model_path = "dummy_model_check.gguf"
    model = LlamaCppModel(model_path)

    if model.is_loaded():
        logger.info("llama.cpp model loaded successfully.")
    else:
        logger.error("Failed to load llama.cpp model.")

except Exception as e:
    logger.error(f"An error occurred while checking model loading: {e}", exc_info=True)

finally:
    # Очистка фиктивного файла (опционально, можно оставить для следующих запусков)
    # logger.info("Attempting cleanup...")
    # if os.path.exists(dummy_model_filename):
    #     try:
    #         os.remove(dummy_model_filename)
    #         logger.info(f"Cleaned up dummy model file: {dummy_model_filename}")
    #     except Exception as e:
    #         logger.warning(f"Could not remove dummy file '{dummy_model_filename}': {e}")
    logger.info("Script finished.") # Add a final message
