# GC-Forged-Pylot

## 🇷🇺 Описание
GC-Forged-Pylot — это автономный помощник для программирования с искусственным интеллектом, который работает локально, обеспечивая максимальную конфиденциальность данных пользователя. Проект построен на базе **llama.cpp** и предоставляет мощные инструменты для ускорения разработки.

### Ключевые особенности:
- **Конфиденциальность**: Полностью локальное выполнение, исключающее утечку данных.
- **Модульная архитектура**:
  - **GC-Core**: Взаимодействие с языковыми моделями.
  - **Forged-Bridge**: Интеграция с редакторами кода.
  - **Pylot-Agent**: Автономный агент для выполнения задач.
- **Инструменты анализа кода**: Семантический поиск, рефакторинг, генерация тестов и документации.

---

## 🇬🇧 Description
GC-Forged-Pylot is an autonomous AI-powered coding assistant designed to run locally, ensuring maximum confidentiality of user data. Built on **llama.cpp**, it provides powerful tools to accelerate development.

### Key Features:
- **Confidentiality**: Fully local execution eliminates data leakage.
- **Modular Architecture**:
  - **GC-Core**: Interaction with language models.
  - **Forged-Bridge**: Integration with code editors.
  - **Pylot-Agent**: Autonomous agent for task execution.
- **Code Analysis Tools**: Semantic search, refactoring, test generation, and documentation creation.

---

## 🇷🇺 Установка
### Предварительные требования:
- Python версии 3.8 или выше.
- Минимум 8 ГБ ОЗУ (рекомендуется 16 ГБ).
- GPU (опционально): NVIDIA CUDA или AMD ROCm.

### Шаги:
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/NickScherbakov/GC-Forged-Pylot.git
   cd GC-Forged-Pylot
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Скачайте модель **GGUF** и поместите её в папку `models/`.
4. Запустите основной скрипт:
   ```bash
   python main.py --model models/your_model.gguf
   ```

---

## 🇬🇧 Installation
### Prerequisites:
- Python 3.8 or higher.
- At least 8 GB of RAM (16 GB recommended).
- GPU (optional): NVIDIA CUDA or AMD ROCm.

### Steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/NickScherbakov/GC-Forged-Pylot.git
   cd GC-Forged-Pylot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Download the **GGUF** model and place it in the `models/` folder.
4. Run the main script:
   ```bash
   python main.py --model models/your_model.gguf
   ```

---

## 🇷🇺 Для участников
### Как внести вклад:
1. Ознакомьтесь с [документацией](./docs/README.ru.md).
2. Создайте fork репозитория и предложите изменения через pull request.
3. Открывайте issues для обсуждения новых функций и исправления ошибок.

---

## 🇬🇧 For Contributors
### How to contribute:
1. Review the [documentation](./docs/README.md).
2. Fork the repository and propose changes via a pull request.
3. Open issues to discuss new features and fix bugs.

---

## 🇷🇺 Для инвесторов и спонсоров
GC-Forged-Pylot предоставляет мощные возможности локального искусственного интеллекта, сохраняя конфиденциальность данных. Поддержите проект, чтобы ускорить разработку новых функций и улучшений.

---

## 🇬🇧 For Investors and Sponsors
GC-Forged-Pylot provides powerful local AI capabilities while ensuring data privacy. Support the project to accelerate the development of new features and improvements.

---

## 🇷🇺 Лицензия
Этот проект лицензирован под лицензией MIT.

---

## 🇬🇧 License
This project is licensed under the MIT License.