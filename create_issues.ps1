# Скрипт для автоматического создания задач в GitHub с использованием GitHub CLI

# Убедитесь, что вы авторизованы в GitHub CLI
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Вы не авторизованы в GitHub CLI. Пожалуйста, выполните 'gh auth login'." -ForegroundColor Red
    exit 1
}

# Репозиторий, в котором будут созданы задачи
$repository = "NickScherbakov/GC-Forged-Pylot"

# Список задач для создания
$issues = @(
    @{
        title = "Implement full functionality for LlamaLLM class"
        body = "Provide detailed steps for implementing the full functionality of the LlamaLLM class. This includes ensuring compatibility with llama.cpp and seamless integration with other modules in GC-Forged-Pylot."
        labels = "good first issue,enhancement"
    },
    @{
        title = "Add support for external llama.cpp API server"
        body = "Implement functionality to connect GC-Forged-Pylot to an external llama.cpp API server. This should include configuration options and documentation for users."
        labels = "good first issue,feature"
    },
    @{
        title = "Improve documentation for installation and usage"
        body = "Enhance the project's documentation with detailed steps for installation, configuration, and usage examples. Make it user-friendly for both beginners and advanced users."
        labels = "good first issue,documentation"
    }
)

# Создание задач
foreach ($issue in $issues) {
    Write-Host "Создаётся задача: $($issue.title)" -ForegroundColor Green
    gh issue create `
        --repo $repository `
        --title $($issue.title) `
        --body $($issue.body) `
        --label $($issue.labels)

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Задача '$($issue.title)' успешно создана!" -ForegroundColor Cyan
    } else {
        Write-Host "Не удалось создать задачу '$($issue.title)'." -ForegroundColor Red
    }
}