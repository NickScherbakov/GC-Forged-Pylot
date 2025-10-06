"""
GC-Forged Pylot - Plugin System
================================

Модуль системы плагинов для расширения функциональности проекта.
"""

from .plugin_interface import PluginInterface, PluginManager
from .plugin_loader import load_plugin, discover_plugins

__all__ = ['PluginInterface', 'PluginManager', 'load_plugin', 'discover_plugins']
