# Руководство по разработке плагинов для GC-Forged-Pylot

## Введение

Система плагинов GC-Forged-Pylot позволяет расширять функциональность проекта без изменения основного кода. Плагины могут добавлять новые инструменты, обрабатывать события, модифицировать поведение системы и многое другое.

## Структура плагина

Каждый плагин должен наследоваться от базового класса `PluginInterface`:

```python
from src.plugins.plugin_interface import PluginInterface, Task, Tool

class MyPlugin(PluginInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "my_plugin"
        self.version = "1.0.0"
        self.author = "Your Name"
        self.description = "Описание плагина"
    
    def on_load(self):
        """Инициализация плагина"""
        print(f"Плагин {self.name} загружен")
```

## Доступные хуки

### 1. on_load()
Вызывается при загрузке плагина. Используйте для инициализации ресурсов.

```python
def on_load(self):
    self.database = self.connect_to_database()
    self.cache = {}
```

### 2. on_unload()
Вызывается при выгрузке плагина. Используйте для очистки ресурсов.

```python
def on_unload(self):
    self.database.close()
    self.cache.clear()
```

### 3. on_task_start(task)
Вызывается перед началом выполнения задачи.

```python
def on_task_start(self, task):
    print(f"Начинаем задачу: {task.description}")
    return {"start_time": time.time()}
```

### 4. on_task_complete(task, result)
Вызывается после завершения задачи.

```python
def on_task_complete(self, task, result):
    print(f"Задача завершена с результатом: {result}")
    self.save_to_history(task, result)
```

### 5. on_task_error(task, error)
Вызывается при ошибке выполнения задачи.

```python
def on_task_error(self, task, error):
    print(f"Ошибка: {error}")
    self.send_alert(task, error)
    return "Ошибка обработана плагином"
```

### 6. on_improvement_cycle(cycle_data)
Вызывается во время цикла самосовершенствования.

```python
def on_improvement_cycle(self, cycle_data):
    iteration = cycle_data.get("iteration")
    print(f"Цикл улучшения #{iteration}")
    return {"additional_metrics": self.calculate_metrics()}
```

### 7. on_code_generation(prompt, generated_code)
Вызывается после генерации кода AI.

```python
def on_code_generation(self, prompt, generated_code):
    # Добавить комментарии или форматирование
    formatted_code = self.format_code(generated_code)
    return formatted_code
```

### 8. add_tools()
Добавляет новые инструменты в систему.

```python
def add_tools(self):
    def my_tool_function(param):
        return f"Processing {param}"
    
    tool = Tool(
        name="my_tool",
        description="Описание инструмента",
        function=my_tool_function
    )
    return [tool]
```

## Примеры плагинов

### Пример 1: Discord Notifications

```python
class DiscordNotificationPlugin(PluginInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "discord_notifications"
        self.version = "1.0.0"
        self.webhook_url = config.get("webhook_url")
    
    def on_load(self):
        from discord_webhook import DiscordWebhook
        self.webhook = DiscordWebhook
    
    def on_task_complete(self, task, result):
        webhook = self.webhook(url=self.webhook_url)
        webhook.content = f"✅ Задача завершена: {task.description}"
        webhook.execute()
```

### Пример 2: Code Review Assistant

```python
class CodeReviewPlugin(PluginInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "code_review_assistant"
        self.version = "1.0.0"
    
    def on_code_generation(self, prompt, generated_code):
        # Автоматический ревью кода
        issues = self.analyze_code(generated_code)
        
        if issues:
            print(f"⚠️  Найдено проблем: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")
        
        return generated_code
    
    def analyze_code(self, code):
        issues = []
        
        # Простые проверки
        if "TODO" in code:
            issues.append("Найдены TODO комментарии")
        
        if "print(" in code and "debug" not in code.lower():
            issues.append("Использование print() вместо logging")
        
        return issues
```

### Пример 3: Performance Monitor

```python
import time

class PerformanceMonitorPlugin(PluginInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "performance_monitor"
        self.version = "1.0.0"
        self.task_times = {}
    
    def on_task_start(self, task):
        self.task_times[id(task)] = time.time()
    
    def on_task_complete(self, task, result):
        start_time = self.task_times.get(id(task))
        if start_time:
            duration = time.time() - start_time
            print(f"⏱️  Задача выполнена за {duration:.2f} секунд")
            del self.task_times[id(task)]
```

### Пример 4: Git Auto-Commit

```python
import subprocess

class GitAutoCommitPlugin(PluginInterface):
    def __init__(self, config):
        super().__init__(config)
        self.name = "git_auto_commit"
        self.version = "1.0.0"
        self.auto_commit = config.get("auto_commit", False)
    
    def on_improvement_cycle(self, cycle_data):
        if not self.auto_commit:
            return
        
        iteration = cycle_data.get("iteration")
        module_name = cycle_data.get("module_name", "unknown")
        
        # Автоматический коммит
        try:
            subprocess.run(["git", "add", "."])
            subprocess.run([
                "git", "commit", "-m",
                f"Auto-commit: Improvement cycle #{iteration} - {module_name}"
            ])
            print("✅ Изменения закоммичены")
        except Exception as e:
            print(f"❌ Ошибка при коммите: {e}")
```

## Регистрация плагина

```python
from src.plugins import PluginManager

# Создать менеджер плагинов
manager = PluginManager()

# Создать конфигурацию плагина
config = {
    "webhook_url": "https://discord.com/api/webhooks/...",
    "auto_commit": True
}

# Создать и зарегистрировать плагин
plugin = MyPlugin(config)
manager.register_plugin(plugin)

# Использование
task = Task(description="Test task", type="code_generation")
manager.trigger_hook("on_task_start", task)
```

## Конфигурация плагинов

Создайте файл `config/plugins.json`:

```json
{
  "plugins": [
    {
      "name": "discord_notifications",
      "enabled": true,
      "config": {
        "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK"
      }
    },
    {
      "name": "code_review_assistant",
      "enabled": true,
      "config": {
        "strict_mode": true,
        "auto_fix": false
      }
    },
    {
      "name": "performance_monitor",
      "enabled": true,
      "config": {
        "log_to_file": true,
        "threshold_seconds": 10
      }
    }
  ]
}
```

## Лучшие практики

1. **Обработка ошибок**: Всегда оборачивайте код в try-except блоки
2. **Производительность**: Избегайте блокирующих операций в хуках
3. **Документация**: Документируйте конфигурационные параметры
4. **Версионирование**: Используйте семантическое версионирование
5. **Тестирование**: Создавайте тесты для ваших плагинов
6. **Зависимости**: Указывайте требуемые библиотеки в docstring

## Публикация плагина

1. Создайте репозиторий на GitHub
2. Добавьте README с инструкциями по установке
3. Добавьте примеры использования
4. Создайте issue в основном репозитории GC-Forged-Pylot с тегом `plugin`
5. Ваш плагин будет добавлен в официальную галерею плагинов

## Дополнительные ресурсы

- [API Reference](../src/plugins/plugin_interface.py)
- [Примеры плагинов](../examples/plugins/)
- [Галерея плагинов сообщества](https://github.com/NickScherbakov/GC-Forged-Pylot/wiki/Plugin-Gallery)

## Поддержка

Если у вас возникли вопросы:
- Откройте issue на GitHub
- Присоединяйтесь к дискуссиям
- Свяжитесь с командой разработчиков

---

**Создавайте потрясающие плагины и делитесь ими с сообществом!** 🚀
