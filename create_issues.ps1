# Скрипт для создания задачи "embeddings&finetunings" в репозитории GC-Forged-Pylot

# Проверяем авторизацию в GitHub CLI
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Требуется авторизация в GitHub CLI. Выполните 'gh auth login'." -ForegroundColor Red
    exit 1
}

# Репозиторий
$repository = "NickScherbakov/GC-Forged-Pylot"

# Задача
$title = "Develop embeddings&finetunings subsystem"
$body = @"
### Technical Specification
The goal is to create a subsystem for handling embeddings and fine-tuning within the GC-Forged-Pylot project. This subsystem will work with llama.cpp to enable real-time model updates and fine-tuning based on interaction data.

#### Requirements:
1. Data collection and storage.
2. Embeddings generation and updates.
3. Fine-tuning automation (local and via API).
4. Integration with llama.cpp API-server.

#### Deliverables:
- An operational subsystem for embeddings and fine-tuning.
- Updated llama.cpp model in .gguf format.
- Comprehensive documentation for developers.
"@
$labels = "enhancement,good first issue,feature"

# Создаем задачу
gh issue create `
    --repo $repository `
    --title $title `
    --body $body `
    --label $labels

if ($LASTEXITCODE -eq 0) {
    Write-Host "Задача успешно создана!" -ForegroundColor Green
} else {
    Write-Host "Не удалось создать задачу." -ForegroundColor Red
}