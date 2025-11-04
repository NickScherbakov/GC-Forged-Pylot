#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple tool for getting Git repository status."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from ..tool_manager import Tool


class GitStatusTool(Tool):
    """Returns aggregated git repository status."""

    def __init__(self, name: str = "git_status", description: str = "Показывает статус git", config: Dict[str, Any] | None = None):
        super().__init__(name=name, description=description, config=config)

    def execute(self, path: str = ".", short: bool = True, **_: Any) -> Dict[str, Any]:
        repo_path = Path(path)
        if not repo_path.exists():
            return {"success": False, "error": f"Путь {repo_path} не существует"}

        cmd = ["git", "status"]
        if short:
            cmd.append("--short")

        try:
            output = subprocess.check_output(cmd, cwd=str(repo_path), stderr=subprocess.STDOUT, text=True)
            clean = not output.strip()
            return {
                "success": True,
                "clean": clean,
                "summary": output.strip(),
            }
        except subprocess.CalledProcessError as exc:
            return {
                "success": False,
                "error": exc.output.strip(),
                "returncode": exc.returncode,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "git не найден в PATH",
            }
