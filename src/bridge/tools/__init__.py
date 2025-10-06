#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Инструменты для работы с кодом
====================================

Пакет инструментов для анализа, рефакторинга и генерации кода.

Автор: GC-Forged Pylot Team
Дата: 2025
Лицензия: MIT
"""

from typing import List

from .code_parser import CodeParser  # noqa: F401

__all__: List[str] = ["CodeParser"]

try:  # pragma: no cover - опциональные инструменты
    from .code_refactor import CodeRefactor  # type: ignore # noqa: F401

    __all__.append("CodeRefactor")
except ImportError:
    pass

try:  # pragma: no cover - опциональные инструменты
    from .semantic_search import SemanticSearch  # type: ignore # noqa: F401

    __all__.append("SemanticSearch")
except ImportError:
    pass

try:  # pragma: no cover - опциональные инструменты
    from .test_generator import TestGenerator  # type: ignore # noqa: F401

    __all__.append("TestGenerator")
except ImportError:
    pass

try:  # pragma: no cover - опциональные инструменты
    from .documentation_generator import DocumentationGenerator  # type: ignore # noqa: F401

    __all__.append("DocumentationGenerator")
except ImportError:
    pass

try:  # pragma: no cover - опциональные инструменты
    from .git_status import GitStatusTool  # noqa: F401

    __all__.append("GitStatusTool")
except ImportError:
    pass