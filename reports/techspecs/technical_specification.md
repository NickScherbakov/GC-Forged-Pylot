# Техническое задание на доработку проекта GC-Forged-Pylot

## 1. Общая информация о проекте

**GC-Forged-Pylot** — локальная альтернатива GitHub Copilot на базе llama.cpp, обеспечивающая конфиденциальность кода пользователя. Проект имеет модульную архитектуру из трех компонентов:

- **GC-Core**: Взаимодействие с LLM моделями
- **Forged-Bridge**: Интеграция с редакторами кода
- **Pylot-Agent**: Автономный агент для выполнения задач

На основе анализа отчетов выявлено несколько ключевых областей, требующих доработки.

## 2. Задачи на доработку

### 2.1. Интеграция с llama.cpp

**Текущая ситуация**: Реализованы заглушки без полноценной функциональности.

**Требования**:
- Завершить реализацию класса `LlamaLLM` в `llm_llama_cpp.py`
- Реализовать полноценную функциональность `LlamaServer` в `server.py`
- Добавить поддержку потоковой генерации текста
- Реализовать эффективное управление памятью для работы с большими моделями
- Добавить конфигурацию для оптимизаций на различном оборудовании (AVX-512, ROCm)

```python
# Пример ожидаемой реализации метода в LlamaLLM
def generate(self, prompt: str, **kwargs) -> LLMResponse:
    # Используем llama-cpp-python для генерации
    params = {
        "max_tokens": kwargs.get("max_tokens", 256),
        "temperature": kwargs.get("temperature", 0.7),
        "top_p": kwargs.get("top_p", 0.95),
        "stream": kwargs.get("stream", False),
        # Другие параметры
    }
    
    try:
        # Вызов API llama.cpp
        result = self.llm_instance.generate(prompt, **params)
        return LLMResponse(
            text=result.text,
            tokens_used=result.usage.total_tokens,
            finish_reason=result.finish_reason
        )
    except Exception as e:
        # Обработка ошибок
```

### 2.2. Поддержка внешнего API сервера llama.cpp

**Текущая ситуация**: Базовая поддержка без полноценной интеграции.

**Требования**:
- Доработать класс для взаимодействия с внешним API-сервером llama.cpp
- Реализовать настраиваемые параметры соединения (IP, порт, таймауты)
- Добавить поддержку аутентификации при подключении к серверу
- Реализовать обработку ошибок сетевого взаимодействия
- Поддержать потоковую генерацию через внешний API

```python
class ExternalLlamaAPIClient(LLMInterface):
    def __init__(self, api_url: str, api_key: str = None, timeout: int = 30):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        payload = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "stream": kwargs.get("stream", False)
        }
        
        try:
            response = await self.session.post(
                f"{self.api_url}/v1/completions",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            
            return LLMResponse(
                text=result["choices"][0]["text"],
                tokens_used=result.get("usage", {}).get("total_tokens", 0),
                finish_reason=result["choices"][0].get("finish_reason", "unknown")
            )
        except Exception as e:
            # Обработка сетевых ошибок и ошибок API
```

### 2.3. Интеграция с VS Code

**Текущая ситуация**: Абстрактные коннекторы без IDE-специфичных компонентов.

**Требования**:
- Доработать файл `vscode.py` с полной интеграцией с VS Code API
- Реализовать расширение VS Code, которое:
  - Взаимодействует с локальным сервером GC-Forged-Pylot
  - Отображает подсказки в редакторе
  - Поддерживает автодополнение кода
  - Обеспечивает обратную связь для улучшения подсказок
- Реализовать механизм подключения к запущенному процессу VS Code
- Добавить настройки для выбора между встроенным и внешним llama.cpp сервером

```typescript
// Пример кода для расширения VS Code
import * as vscode from 'vscode';
import { PylotClient } from './pylot-client';

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('gcForgedPylot');
    const serverUrl = config.get('serverUrl') || 'http://localhost:8080';
    const useExternalLlama = config.get('useExternalLlama') || false;
    const externalLlamaUrl = config.get('externalLlamaUrl') || 'http://localhost:8000';
    
    const client = new PylotClient(serverUrl, {
        useExternalLlama,
        externalLlamaUrl
    });
    
    const provider = vscode.languages.registerCompletionItemProvider(
        [{ scheme: 'file' }],
        {
            provideCompletionItems(document, position) {
                // Получение контекста редактора
                // Отправка запроса к GC-Forged-Pylot
                // Преобразование результата в CompletionItems
            }
        }
    );
    
    context.subscriptions.push(provider);
}
```

### 2.4. Инструменты для работы с кодом

**Текущая ситуация**: Отсутствуют специализированные инструменты для анализа кода.

**Требования**:
- Добавить следующие инструменты через систему `ToolManager`:
  - **CodeParser**: Синтаксический анализ кода с поддержкой популярных языков
  - **CodeRefactor**: Инструменты рефакторинга (переименование, извлечение метода и т.д.)
  - **SemanticSearch**: Поиск по кодовой базе с учетом семантики
  - **TestGenerator**: Автоматическая генерация юнит-тестов
  - **DocumentationGenerator**: Генерация документации для кода

```python
class CodeParser(Tool):
    def __init__(self):
        super().__init__(name="code_parser", description="Parse and analyze code")
        # Инициализация парсеров для различных языков
        
    def execute(self, code: str, language: str = None, **kwargs) -> Dict:
        """
        Анализирует код и возвращает AST или другую структуру
        """
        # Определение языка, если не указан
        # Выбор соответствующего парсера
        # Анализ кода и возвращение структурированного представления
```

### 2.5. Оптимизация производительности

**Текущая ситуация**: Отсутствуют конкретные оптимизации для локального выполнения.

**Требования**:
- Реализовать кэширование результатов запросов
- Добавить опцию quantization для моделей (4-бит, 8-бит)
- Реализовать адаптивную загрузку моделей в зависимости от доступной памяти
- Добавить поддержку многопоточной обработки запросов
- Оптимизировать использование GPU через CUDA/ROCm
- Реализовать балансировку нагрузки при использовании внешних API

```python
class ModelCache:
    def __init__(self, max_size=100, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        
    def get(self, key):
        # Получение из кэша с проверкой TTL
        
    def set(self, key, value):
        # Добавление в кэш с проверкой размера и удалением устаревших записей
```

### 2.6. Улучшение системы памяти

**Текущая ситуация**: Базовая реализация без продвинутых возможностей.

**Требования**:
- Улучшить `memory.py`, добавив:
  - Долгосрочное хранение контекстов
  - Векторное хранилище на основе эмбеддингов
  - Приоритизацию информации по релевантности
  - Интеграцию с внешними базами знаний

```python
class EnhancedMemory:
    def __init__(self, config):
        self.short_term = ShortTermMemory(config.get("short_term_size", 10))
        self.long_term = VectorMemory(
            dimension=config.get("embedding_dimension", 1536),
            similarity_threshold=config.get("similarity_threshold", 0.85)
        )
        self.embedding_provider = EmbeddingProvider(config.get("embedding_model"))
    
    def add(self, content, metadata=None):
        # Добавление в краткосрочную память
        # Создание эмбеддингов
        # Сохранение в долгосрочную память
    
    def retrieve(self, query, limit=5):
        # Поиск релевантной информации
```

### 2.7. Конфигурация и управление

**Текущая ситуация**: Простое управление без гибких настроек.

**Требования**:
- Разработать унифицированный конфигурационный модуль:
  - Поддержка формата YAML/TOML для конфигураций
  - Валидация конфигураций через Pydantic
  - Динамическое обновление настроек без перезапуска
- Создать веб-интерфейс для управления системой:
  - Мониторинг статуса сервиса
  - Просмотр логов
  - Управление моделями
  - Настройка параметров генерации

```python
class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.validators = {}
        
    def _load_config(self):
        # Загрузка конфигурации из файла
        
    def register_validator(self, section: str, validator: Type[BaseModel]):
        # Регистрация валидатора для секции конфигурации
        
    def get(self, section: str, key: str = None, default=None):
        # Получение значения из конфигурации
        
    def update(self, section: str, key: str, value):
        # Обновление значения в конфигурации с валидацией
```

### 2.8. Другие улучшения

**Требуется**:
- Синхронизировать `requirements.txt` и `setup.py`
- Улучшить документацию кода
- Добавить юнит-тесты и интеграционные тесты
- Создать примеры использования для основных компонентов
- Реализовать систему логирования с разными уровнями детализации

## 3. Технические требования

### 3.1. Поддерживаемые платформы
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS (Big Sur+)

### 3.2. Требования к оборудованию
- CPU: 4+ ядер, желательно с поддержкой AVX2/AVX-512
- RAM: минимум 8 ГБ, рекомендуется 16+ ГБ
- GPU: опционально, NVIDIA с CUDA или AMD с ROCm
- SSD: минимум 10 ГБ свободного места

### 3.3. Технический стек
- Python 3.8+
- llama-cpp-python для интеграции с llama.cpp
- FastAPI и Uvicorn для API
- TypeScript для расширения VS Code
- Pydantic для валидации данных
- Requests для HTTP-запросов
- NumPy для векторных операций
- SQLite/PostgreSQL для хранения данных
- React для веб-интерфейса

## 4. Структура проекта после доработки

```
GC-Forged-Pylot/
├── src/
│   ├── core/
│   │   ├── llm_interface.py         # Абстрактный интерфейс LLM
│   │   ├── llm_llama_cpp.py         # Полная реализация для llama.cpp
│   │   ├── external_llama_api.py    # Модуль для работы с внешним llama.cpp API
│   │   ├── server.py                # LlamaServer с полной функциональностью
│   │   ├── memory.py                # Улучшенная система памяти
│   │   ├── planner.py               # Система планирования
│   │   ├── reasoning.py             # Система рассуждений
│   │   └── executor.py              # Исполнитель планов
│   ├── bridge/
│   │   ├── api_connector.py         # Коннектор к внешним API
│   │   ├── tool_manager.py          # Улучшенный менеджер инструментов
│   │   ├── vscode.py                # Полная интеграция с VS Code
│   │   └── tools/                   # Новые инструменты для работы с кодом
│   │       ├── code_parser.py
│   │       ├── code_refactor.py
│   │       ├── semantic_search.py
│   │       └── test_generator.py
│   ├── config/
│   │   ├── config_manager.py        # Менеджер конфигураций
│   │   ├── validators.py            # Классы валидации
│   │   └── default_config.yaml      # Конфигурация по умолчанию
│   ├── pylot-agent/
│   │   ├── agent.py                 # Главный агент с улучшенной логикой
│   │   └── tasks.py                 # Определение задач
│   └── web/                         # Веб-интерфейс для управления
│       ├── app.py
│       ├── routes.py
│       └── static/
├── vscode-extension/                # Расширение для VS Code
├── tests/                           # Модульные и интеграционные тесты
├── examples/                        # Примеры использования
└── docs/                            # Улучшенная документация
```

## 5. Результаты и критерии приемки

### 5.1. Ожидаемые результаты
- Полнофункциональная система для локального запуска языковых моделей
- Поддержка подключения к внешнему llama.cpp API серверу
- Интеграция с VS Code с поддержкой автодополнения кода
- Набор инструментов для анализа и модификации кода
- Оптимизированная работа на стандартном оборудовании
- Веб-интерфейс для управления системой

### 5.2. Критерии приемки
- Успешная генерация кода на основе промптов
- Время отклика не более 2 секунд для стандартных запросов
- Успешное выполнение всех модульных и интеграционных тестов
- Возможность работы с моделями до 7B параметров на компьютере с 16 ГБ RAM
- Корректная работа как со встроенным, так и с внешним llama.cpp API
- Отказоустойчивость при сетевых проблемах

## 6. API и интерфейсы

### 6.1. REST API
- `/v1/completions` - Получение текстовых дополнений
- `/v1/models` - Получение списка доступных моделей
- `/v1/status` - Получение статуса системы
- `/v1/config` - Управление конфигурацией

### 6.2. WebSocket API
- `/ws/completions` - Потоковая генерация текста

### 6.3. VS Code Extension API
- Автодополнение кода
- Инлайн-подсказки
- Генерация функций и классов
- Рефакторинг кода

## 7. Рекомендации по реализации

1. Начните с интеграции llama.cpp и поддержки внешнего API
2. Затем переходите к оптимизации производительности
3. Далее реализуйте специализированные инструменты для работы с кодом
4. После этого разработайте интеграцию с VS Code
5. В завершение улучшите документацию и тестовое покрытие

Приоритеты следует расставить согласно важности компонентов для конечного пользователя и зависимостей между модулями.

## 8. Безопасность и конфиденциальность

1. Весь пользовательский код должен обрабатываться локально
2. Поддержка шифрования для хранения данных
3. Настраиваемая политика безопасности для внешних API
4. Система логирования без сохранения пользовательского кода