# Automated Setup (auto_setup.ps1)

This document provides usage instructions for the PowerShell setup script in three languages: English, Russian, and Chinese.

---
## English

### Quick Start
```
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1
```

### Parameters
- `-AutoFetchChecksum`: Attempt to download `<ModelUrl>.sha256` automatically and verify.
- `-ModelPreset menu`: Print table of multiple presets and auto-select best by RAM (override with `-SelectPreset <name>`).
- `-SelectPreset <name>`: Used with `-ModelPreset menu` to force a specific preset.
- `-SkipModelDownload`: Skip downloading the model.
- `-ForceReinstallDependencies`: Recreate venv and reinstall dependencies.
- `-NoSmokeTest`: Skip import smoke test for `llama_cpp`.
- `-NoStartScript`: Do not generate `start_server.ps1`.
- `-NoConfig`: Do not generate `config/auto_config.json`.
- `-VerboseSetup`: Extra diagnostic logging.

### Examples
```
# Use existing model, skip download
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -SkipModelDownload -ModelFileName mymodel.gguf

# Force reinstall dependencies and specify custom port
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ForceReinstallDependencies -Port 9000

# Custom model URL

# Menu mode listing presets and auto-select
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu

# Menu mode + force specific preset + auto fetch checksum
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu -SelectPreset tinyllama-q4 -AutoFetchChecksum
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelUrl "https://example.com/model.gguf" -ModelFileName custom.gguf

# Auto-select preset based on RAM
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset auto

# Explicit preset + checksum verification
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset tinyllama-q2 -ModelSha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

### Start Server
```
powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1 -Port 8000
```

---
## Русский

### Быстрый запуск
```
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1
```

### Параметры
- `-ModelUrl <url>`: Свой URL для скачивания модели.
- `-ModelFileName <name>`: Имя файла модели GGUF.
- `-ModelDir <path>`: Каталог для моделей (по умолчанию `models`).
- `-ContextSize <int>`: Размер контекста (по умолчанию `1024`).
- `-ApiKey <string>`: API ключ для `.env` и конфига.
- `-Port <int>`: Порт сервера (по умолчанию `8000`).
- `-ModelPreset <auto|tinyllama-q4|tinyllama-q2>`: Выбор предустановленного варианта модели (auto по ОЗУ).
- `-ModelSha256 <hex>`: Контрольная сумма SHA256 для проверки целостности.
- `-SkipModelDownload`: Пропустить скачивание модели.
- `-ForceReinstallDependencies`: Полная переустановка зависимостей.
- `-NoSmokeTest`: Пропустить пробный импорт `llama_cpp`.
- `-NoStartScript`: Не создавать `start_server.ps1`.
- `-NoConfig`: Не создавать `config/auto_config.json`.
- `-VerboseSetup`: Расширенный вывод.

### Примеры
```
# Использовать существующую модель
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -SkipModelDownload -ModelFileName mymodel.gguf

# Переустановка зависимостей и порт 9000
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ForceReinstallDependencies -Port 9000

# Скачивание с пользовательского URL
- `-AutoFetchChecksum`: Попытка авто-загрузки файла `<ModelUrl>.sha256`.
- `-ModelPreset menu`: Показать таблицу пресетов и авто-выбор по ОЗУ (переопределить `-SelectPreset`).
- `-SelectPreset <name>`: Явный выбор пресета с режимом `menu`.
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelUrl "https://example.com/model.gguf" -ModelFileName custom.gguf

# Автовыбор пресета по ОЗУ
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset auto

# Явный пресет + проверка контрольной суммы
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset tinyllama-q2 -ModelSha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# Режим меню (таблица пресетов)
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu

# Меню + явный выбор + авто-получение контрольной суммы
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu -SelectPreset tinyllama-q4 -AutoFetchChecksum
```

### Запуск сервера
```
powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1 -Port 8000
```

---
## 中文

### 快速开始
```
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1
```

### 参数
- `-ModelUrl <url>`: 自定义模型下载地址。
- `-AutoFetchChecksum`: 自动尝试下载 `<ModelUrl>.sha256` 验证。
- `-ModelPreset menu`: 输出可选模型表并按内存自动选择 (可用 `-SelectPreset <name>` 强制指定)。
- `-SelectPreset <name>`: 与 `menu` 模式一起使用，强制选择指定预设。
- `-ModelFileName <name>`: GGUF 模型文件名。
- `-ModelDir <path>`: 模型目录 (默认 `models`)。
- `-ContextSize <int>`: 上下文大小 (默认 `1024`)。
- `-ApiKey <string>`: 写入 `.env` 与配置的 API 密钥。
- `-Port <int>`: 服务器端口 (默认 `8000`)。
- `-ModelPreset <auto|tinyllama-q4|tinyllama-q2>`: 预设模型选择 (auto 根据内存)。
- `-ModelSha256 <hex>`: 模型文件的 SHA256 校验值。
- `-SkipModelDownload`: 跳过模型下载。
- `-ForceReinstallDependencies`: 重新安装所有依赖。
- `-NoSmokeTest`: 跳过 `llama_cpp` 试导入。
- `-NoStartScript`: 不生成启动脚本。
- `-NoConfig`: 不生成 `auto_config.json`。
- `-VerboseSetup`: 输出更多日志。

### 示例
```
# 使用已有模型，跳过下载
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -SkipModelDownload -ModelFileName mymodel.gguf

# 强制重新安装依赖并使用 9000 端口
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ForceReinstallDependencies -Port 9000

# 自定义模型 URL
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelUrl "https://example.com/model.gguf" -ModelFileName custom.gguf

# 内存自动选择预设
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset auto

# 指定预设并校验 SHA256
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset tinyllama-q2 -ModelSha256 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

# 菜单模式 (列出所有预设)
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu

# 菜单模式 + 指定预设 + 自动获取校验值
powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1 -ModelPreset menu -SelectPreset tinyllama-q4 -AutoFetchChecksum
```

### 启动服务器
```
powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1 -Port 8000
```

---
### Notes
- Ensure Python 3.8–3.11 is installed and available in PATH.
- If `llama-cpp-python` fails to build, install Visual Studio Build Tools and CMake.
- Adjust `ContextSize` downward (e.g. 768) for low RAM systems.
