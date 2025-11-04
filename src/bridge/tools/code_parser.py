#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GC-Forged Pylot - Code Syntax Analysis Tool
=======================================================

Tool for analyzing code in various programming languages.
Supports source code parsing and AST construction.

Author: GC-Forged Pylot Team
Date: 2025
License: MIT
"""

import os
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import tempfile
import subprocess

# Импортируем основные зависимости
try:
    import tree_sitter
except ImportError:
    tree_sitter = None

# Инициализация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CodeParser")

# Базовый класс инструмента
class Tool:
    """
    Базовый класс для всех инструментов.
    """
    
    def __init__(self, name: str, description: str):
        """
        Инициализирует инструмент.
        
        Args:
            name: Имя инструмента
            description: Описание инструмента
        """
        self.name = name
        self.description = description


class CodeParser(Tool):
    """
    Инструмент для синтаксического анализа кода.
    """
    
    def __init__(self):
        """
        Инициализирует парсер кода.
        """
        super().__init__(
            name="code_parser",
            description="Синтаксический анализ кода с поддержкой популярных языков"
        )
        
        # Флаг доступности tree-sitter
        self.tree_sitter_available = tree_sitter is not None
        
        # Инициализация парсеров для разных языков
        self.parsers = {}
        self.languages = {}
        
        # Загружаем парсеры, если tree-sitter доступен
        if self.tree_sitter_available:
            self._initialize_tree_sitter()
        else:
            logger.warning(
                "Tree-sitter не установлен. Некоторые функции парсинга будут ограничены. "
                "Установите tree-sitter: pip install tree-sitter"
            )
        
        # Другие доступные парсеры
        self._initialize_fallback_parsers()
        
        logger.info("Инструмент CodeParser инициализирован")
    
    def _initialize_tree_sitter(self):
        """
        Инициализирует парсеры tree-sitter для различных языков.
        """
        if not self.tree_sitter_available:
            return
            
        try:
            # Пути к языковым грамматикам
            languages_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "resources",
                "tree-sitter-languages"
            )
            
            # Проверяем, существует ли директория
            if not os.path.exists(languages_dir):
                os.makedirs(languages_dir, exist_ok=True)
            
            # Загружаем доступные языковые грамматики
            language_configs = {
                "python": "tree-sitter-python",
                "javascript": "tree-sitter-javascript",
                "typescript": "tree-sitter-typescript",
                "cpp": "tree-sitter-cpp",
                "c": "tree-sitter-c",
                "java": "tree-sitter-java",
                "ruby": "tree-sitter-ruby",
                "go": "tree-sitter-go",
                "rust": "tree-sitter-rust",
                "php": "tree-sitter-php"
            }
            
            for lang_name, repo_name in language_configs.items():
                try:
                    # Проверяем, загружена ли уже эта грамматика
                    language_lib_path = os.path.join(languages_dir, f"{lang_name}.so")
                    
                    if not os.path.exists(language_lib_path):
                        # Если грамматика не загружена, можно скачать и собрать её
                        # Но для простоты в этой реализации просто логируем отсутствие
                        logger.warning(f"Грамматика для языка {lang_name} не найдена в {language_lib_path}")
                        continue
                    
                    # Загружаем языковую грамматику
                    language = tree_sitter.Language(language_lib_path)
                    parser = tree_sitter.Parser()
                    parser.set_language(language)
                    
                    self.languages[lang_name] = language
                    self.parsers[lang_name] = parser
                    logger.info(f"Загружен парсер tree-sitter для языка {lang_name}")
                    
                except Exception as e:
                    logger.error(f"Не удалось загрузить парсер для {lang_name}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации tree-sitter: {str(e)}")
    
    def _initialize_fallback_parsers(self):
        """
        Инициализирует запасные парсеры для языков, не поддерживаемых tree-sitter.
        """
        # Python имеет встроенный модуль ast
        if "python" not in self.parsers:
            self.parsers["python"] = "ast"
            logger.info("Загружен встроенный парсер ast для Python")
    
    def execute(self, code: str, language: str = None, **kwargs) -> Dict[str, Any]:
        """
        Выполняет синтаксический анализ кода.
        
        Args:
            code: Исходный код для анализа
            language: Язык программирования (python, javascript и т.д.)
            **kwargs: Дополнительные параметры
            
        Returns:
            Dict[str, Any]: Результат анализа
        """
        # Определяем язык, если не указан
        if language is None:
            language = self._detect_language(code)
        
        # Нормализуем название языка
        language = language.lower()
        
        # Проверяем, поддерживается ли язык
        if language not in self.parsers and language not in ["python"]:
            return {
                "success": False,
                "error": f"Язык {language} не поддерживается",
                "language": language
            }
        
        # Выполняем анализ в зависимости от языка и доступных парсеров
        try:
            if language == "python":
                if self.tree_sitter_available and "python" in self.parsers and not isinstance(self.parsers["python"], str):
                    return self._parse_with_tree_sitter(code, language)
                else:
                    return self._parse_python_with_ast(code)
            elif self.tree_sitter_available and language in self.parsers:
                return self._parse_with_tree_sitter(code, language)
            else:
                return {
                    "success": False,
                    "error": f"Для языка {language} нет доступного парсера",
                    "language": language
                }
        except Exception as e:
            logger.error(f"Ошибка при выполнении синтаксического анализа: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка анализа: {str(e)}",
                "language": language
            }
    
    def _detect_language(self, code: str) -> str:
        """
        Определяет язык программирования по коду.
        
        Args:
            code: Исходный код
            
        Returns:
            str: Предполагаемый язык программирования
        """
        # Простая эвристика для определения языка
        if "def " in code and ":" in code and "import " in code:
            return "python"
        elif "function" in code and "{" in code and "}" in code:
            if "interface " in code or "type " in code or "<" in code and ">" in code:
                return "typescript"
            else:
                return "javascript"
        elif "#include" in code and (("{" in code and "}" in code) or ";" in code):
            if "class " in code and "public:" in code:
                return "cpp"
            else:
                return "c"
        elif "public class " in code or "private class " in code:
            return "java"
        elif "fn " in code and "->" in code:
            return "rust"
        elif "func " in code and "package " in code:
            return "go"
        elif "<?php" in code:
            return "php"
        elif "require " in code and "end" in code:
            return "ruby"
        
        # По умолчанию предполагаем, что это JavaScript
        return "javascript"
    
    def _parse_with_tree_sitter(self, code: str, language: str) -> Dict[str, Any]:
        """
        Парсит код с использованием tree-sitter.
        
        Args:
            code: Исходный код
            language: Язык программирования
            
        Returns:
            Dict[str, Any]: Результат парсинга
        """
        try:
            parser = self.parsers[language]
            tree = parser.parse(bytes(code, "utf8"))
            
            # Преобразуем дерево в структуру, которую можно сериализовать в JSON
            result = self._tree_to_dict(tree.root_node)
            
            # Добавляем базовую информацию
            structure = self._extract_structure(result, language)
            
            return {
                "success": True,
                "language": language,
                "ast": result,
                "structure": structure
            }
        except Exception as e:
            logger.error(f"Ошибка при парсинге с tree-sitter: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка парсинга: {str(e)}",
                "language": language
            }
    
    def _parse_python_with_ast(self, code: str) -> Dict[str, Any]:
        """
        Парсит Python код с использованием встроенного модуля ast.
        
        Args:
            code: Исходный код Python
            
        Returns:
            Dict[str, Any]: Результат парсинга
        """
        try:
            tree = ast.parse(code)
            
            # Преобразуем AST в словарь
            ast_dict = self._python_ast_to_dict(tree)
            
            # Извлекаем структуру кода
            structure = self._extract_python_structure(tree)
            
            return {
                "success": True,
                "language": "python",
                "ast": ast_dict,
                "structure": structure
            }
        except SyntaxError as e:
            # Обрабатываем синтаксические ошибки
            return {
                "success": False,
                "error": f"Синтаксическая ошибка: {str(e)}",
                "error_line": e.lineno,
                "error_offset": e.offset,
                "language": "python"
            }
        except Exception as e:
            logger.error(f"Ошибка при парсинге Python с ast: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка парсинга: {str(e)}",
                "language": "python"
            }
    
    def _tree_to_dict(self, node) -> Dict[str, Any]:
        """
        Преобразует узел дерева tree-sitter в словарь.
        
        Args:
            node: Узел дерева
            
        Returns:
            Dict[str, Any]: Словарь с информацией об узле
        """
        result = {
            "type": node.type,
            "start_point": {
                "row": node.start_point[0],
                "column": node.start_point[1]
            },
            "end_point": {
                "row": node.end_point[0],
                "column": node.end_point[1]
            },
        }
        
        if len(node.children) == 0:
            result["text"] = node.text.decode('utf8')
        else:
            result["children"] = [self._tree_to_dict(child) for child in node.children]
            
        return result
    
    def _python_ast_to_dict(self, node) -> Dict[str, Any]:
        """
        Преобразует узел Python AST в словарь.
        
        Args:
            node: Узел AST
            
        Returns:
            Dict[str, Any]: Словарь с информацией об узле
        """
        if isinstance(node, ast.AST):
            result = {'type': node.__class__.__name__}
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    result[field] = [self._python_ast_to_dict(item) for item in value]
                elif isinstance(value, ast.AST):
                    result[field] = self._python_ast_to_dict(value)
                else:
                    result[field] = value
            return result
        elif isinstance(node, list):
            return [self._python_ast_to_dict(item) for item in node]
        else:
            return node
    
    def _extract_structure(self, ast_dict: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Извлекает структуру кода из AST.
        
        Args:
            ast_dict: AST в виде словаря
            language: Язык программирования
            
        Returns:
            Dict[str, Any]: Структура кода
        """
        if language == "python":
            return self._extract_python_structure_from_dict(ast_dict)
        elif language in ["javascript", "typescript"]:
            return self._extract_js_structure_from_dict(ast_dict)
        else:
            # Для других языков пока возвращаем базовую информацию
            return {
                "language": language,
                "top_level_elements": []
            }
    
    def _extract_python_structure(self, ast_tree) -> Dict[str, Any]:
        """
        Извлекает структуру Python кода из AST.
        
        Args:
            ast_tree: AST дерево
            
        Returns:
            Dict[str, Any]: Структура кода
        """
        structure = {
            "language": "python",
            "imports": [],
            "classes": [],
            "functions": [],
            "global_variables": []
        }
        
        # Обрабатываем каждый узел верхнего уровня
        for node in ast_tree.body:
            # Импорты
            if isinstance(node, ast.Import):
                for name in node.names:
                    structure["imports"].append({
                        "type": "import",
                        "name": name.name,
                        "asname": name.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    structure["imports"].append({
                        "type": "import_from",
                        "module": node.module,
                        "name": name.name,
                        "asname": name.asname
                    })
            
            # Определения классов
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "methods": [],
                    "class_variables": []
                }
                
                # Добавляем базовые классы, если есть
                if node.bases:
                    class_info["bases"] = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            class_info["bases"].append(base.id)
                
                # Извлекаем методы и переменные класса
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        method_info = {
                            "name": class_node.name,
                            "args": self._extract_function_args(class_node)
                        }
                        class_info["methods"].append(method_info)
                    elif isinstance(class_node, ast.Assign):
                        for target in class_node.targets:
                            if isinstance(target, ast.Name):
                                class_info["class_variables"].append(target.id)
                
                structure["classes"].append(class_info)
            
            # Определения функций
            elif isinstance(node, ast.FunctionDef):
                function_info = {
                    "name": node.name,
                    "args": self._extract_function_args(node)
                }
                structure["functions"].append(function_info)
            
            # Глобальные переменные
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        structure["global_variables"].append({
                            "name": target.id
                        })
        
        return structure
    
    def _extract_function_args(self, func_node) -> List[Dict[str, Any]]:
        """
        Извлекает аргументы функции из узла AST.
        
        Args:
            func_node: Узел функции
            
        Returns:
            List[Dict[str, Any]]: Список аргументов функции
        """
        args = []
        
        # Позиционные аргументы
        for arg in func_node.args.args:
            arg_info = {"name": arg.arg}
            if hasattr(arg, 'annotation') and arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_info["type"] = arg.annotation.id
            args.append(arg_info)
        
        # *args
        if func_node.args.vararg:
            args.append({
                "name": func_node.args.vararg.arg,
                "is_vararg": True
            })
        
        # **kwargs
        if func_node.args.kwarg:
            args.append({
                "name": func_node.args.kwarg.arg,
                "is_kwarg": True
            })
            
        return args
    
    def _extract_python_structure_from_dict(self, ast_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает структуру Python кода из словаря AST.
        
        Args:
            ast_dict: AST в виде словаря
            
        Returns:
            Dict[str, Any]: Структура кода
        """
        structure = {
            "language": "python",
            "imports": [],
            "classes": [],
            "functions": [],
            "global_variables": []
        }
        
        # Здесь должна быть реализация извлечения структуры из словаря AST
        # Упрощенная версия для демонстрации
        
        return structure
    
    def _extract_js_structure_from_dict(self, ast_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает структуру JavaScript/TypeScript кода из словаря AST.
        
        Args:
            ast_dict: AST в виде словаря
            
        Returns:
            Dict[str, Any]: Структура кода
        """
        structure = {
            "language": "javascript/typescript",
            "imports": [],
            "classes": [],
            "functions": [],
            "variables": []
        }
        
        # Здесь должна быть реализация извлечения структуры из словаря AST
        # Упрощенная версия для демонстрации
        
        return structure


# Пример использования
if __name__ == "__main__":
    # Создаем экземпляр парсера
    parser = CodeParser()
    
    # Пример кода для парсинга
    python_code = """
import os
import sys

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def greet(self):
        return f"Hello, my name is {self.name}"

def main():
    person = Person("Alice", 30)
    print(person.greet())

if __name__ == "__main__":
    main()
"""
    
    # Парсим код
    result = parser.execute(python_code, "python")
    
    # Выводим результат
    print(json.dumps(result, indent=2))