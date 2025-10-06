#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example Plugin: Discord Notifications
======================================

Пример плагина для отправки уведомлений в Discord.

Установка:
    pip install discord-webhook

Использование:
    plugin_config = {
        "webhook_url": "https://discord.com/api/webhooks/..."
    }
    plugin = DiscordNotificationPlugin(plugin_config)
    plugin_manager.register_plugin(plugin)
"""

from typing import Dict, Any
import sys
import os

# Добавить родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.plugins.plugin_interface import PluginInterface, Task


class DiscordNotificationPlugin(PluginInterface):
    """Плагин для отправки уведомлений в Discord"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "discord_notifications"
        self.version = "1.0.0"
        self.author = "GC-Forged-Pylot Team"
        self.description = "Отправляет уведомления о задачах в Discord"
        self.webhook_url = config.get("webhook_url", "")
        self.webhook = None
    
    def on_load(self) -> None:
        """Инициализация плагина"""
        if not self.webhook_url:
            print("⚠️  Discord webhook URL не настроен")
            self.enabled = False
            return
        
        try:
            from discord_webhook import DiscordWebhook
            self.webhook = DiscordWebhook
            print(f"✅ Плагин {self.name} загружен успешно")
        except ImportError:
            print("⚠️  Установите discord-webhook: pip install discord-webhook")
            self.enabled = False
    
    def on_task_start(self, task: Task) -> None:
        """Отправить уведомление о начале задачи"""
        if not self.enabled:
            return
        
        try:
            webhook = self.webhook(url=self.webhook_url)
            webhook.content = f"🚀 **Задача начата**\n\n{task.description}"
            webhook.execute()
        except Exception as e:
            print(f"Ошибка отправки в Discord: {e}")
    
    def on_task_complete(self, task: Task, result: Any) -> None:
        """Отправить уведомление о завершении задачи"""
        if not self.enabled:
            return
        
        try:
            webhook = self.webhook(url=self.webhook_url)
            webhook.content = f"✅ **Задача завершена**\n\n{task.description}\n\nРезультат: {result}"
            webhook.execute()
        except Exception as e:
            print(f"Ошибка отправки в Discord: {e}")
    
    def on_task_error(self, task: Task, error: Exception) -> str:
        """Отправить уведомление об ошибке"""
        if not self.enabled:
            return
        
        try:
            webhook = self.webhook(url=self.webhook_url)
            webhook.content = f"❌ **Ошибка выполнения задачи**\n\n{task.description}\n\nОшибка: {str(error)}"
            webhook.execute()
            return "Уведомление об ошибке отправлено в Discord"
        except Exception as e:
            print(f"Ошибка отправки в Discord: {e}")
            return None


if __name__ == "__main__":
    # Демонстрация работы плагина
    print("=== Демонстрация Discord Notification Plugin ===\n")
    
    # Создать плагин (без реального webhook)
    config = {
        "webhook_url": "https://discord.com/api/webhooks/example"  # Замените на реальный URL
    }
    
    plugin = DiscordNotificationPlugin(config)
    print(f"Плагин: {plugin.name} v{plugin.version}")
    print(f"Автор: {plugin.author}")
    print(f"Описание: {plugin.description}")
    print(f"\nИнформация о плагине:")
    print(plugin.get_info())
