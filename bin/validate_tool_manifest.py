#!/usr/bin/env python3
"""Static validation for GC-Forged-Pylot tool manifest files."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # pragma: no cover - environment bootstrap
    sys.path.insert(0, str(REPO_ROOT))

try:  # pragma: no cover - defensive guard in case of refactors
    from src.bridge.tool_manager import Tool
except ImportError as exc:  # pragma: no cover - hard failure
    raise SystemExit(f"Failed to import Tool base class: {exc}") from exc

try:  # pragma: no cover - optional dependency for YAML manifests
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - fallback when PyYAML missing
    yaml = None

TOOL_NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")
PRIMITIVE_TYPES = {"string", "number", "integer", "boolean", "object", "array"}


@dataclass
class ValidationIssue:
    path: Path
    message: str


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifests",
        metavar="MANIFEST",
        type=Path,
        nargs="*",
        help="Path(s) to manifest files. Defaults to config/tool_manifest.json if omitted.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used for module imports and relative path checks.",
    )
    return parser.parse_args(argv)


def load_manifest(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as stream:
            suffix = path.suffix.lower()
            if suffix in {".yaml", ".yml"}:
                if yaml is None:
                    raise SystemExit(
                        "PyYAML is required for YAML manifests. Install with 'pip install pyyaml'."
                    )
                try:
                    return yaml.safe_load(stream)  # type: ignore[no-any-return]
                except yaml.YAMLError as exc:  # type: ignore[attr-defined]
                    raise SystemExit(f"Invalid YAML in {path}: {exc}") from exc
            try:
                return json.load(stream)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    except FileNotFoundError as exc:
        raise SystemExit(f"Manifest not found: {path}") from exc


def validate_manifest(data: Dict[str, Any], manifest_path: Path, repo_root: Path) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    schema_version = data.get("schema_version")
    if schema_version != "1.0":
        issues.append(ValidationIssue(manifest_path, "schema_version must be '1.0'"))

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(ValidationIssue(manifest_path, "metadata must be an object"))
    else:
        for field in ("name", "description"):
            if field not in metadata or not isinstance(metadata[field], str) or not metadata[field].strip():
                issues.append(ValidationIssue(manifest_path, f"metadata.{field} must be a non-empty string"))
        if "maintainers" in metadata and not _is_string_list(metadata["maintainers"]):
            issues.append(ValidationIssue(manifest_path, "metadata.maintainers must be a list of strings"))
        if "tags" in metadata and not _is_string_list(metadata["tags"]):
            issues.append(ValidationIssue(manifest_path, "metadata.tags must be a list of strings"))

    tools = data.get("tools")
    if not isinstance(tools, list) or not tools:
        issues.append(ValidationIssue(manifest_path, "tools must be a non-empty array"))
        return issues

    seen_names: set[str] = set()
    for index, tool in enumerate(tools):
        location = f"tools[{index}]"
        if not isinstance(tool, dict):
            issues.append(ValidationIssue(manifest_path, f"{location} must be an object"))
            continue
        issues.extend(_validate_tool(tool, location, manifest_path, repo_root, seen_names))

    return issues


def _validate_tool(
    tool: Dict[str, Any],
    location: str,
    manifest_path: Path,
    repo_root: Path,
    seen_names: set[str],
) -> Iterable[ValidationIssue]:
    errors: List[ValidationIssue] = []

    name = tool.get("name")
    if not isinstance(name, str) or not TOOL_NAME_PATTERN.match(name):
        errors.append(ValidationIssue(manifest_path, f"{location}.name must match {TOOL_NAME_PATTERN.pattern}"))
    elif name in seen_names:
        errors.append(ValidationIssue(manifest_path, f"Duplicate tool name detected: {name}"))
    else:
        seen_names.add(name)

    description = tool.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(ValidationIssue(manifest_path, f"{location}.description must be a non-empty string"))

    module_path = tool.get("module")
    if not isinstance(module_path, str) or not module_path.strip():
        errors.append(ValidationIssue(manifest_path, f"{location}.module must be a non-empty string"))
    else:
        module_issue = _validate_module(module_path, tool.get("class_name"), repo_root)
        if module_issue:
            errors.append(ValidationIssue(manifest_path, f"{location}.{module_issue}"))

    if "permissions" in tool and not _is_string_list(tool["permissions"]):
        errors.append(ValidationIssue(manifest_path, f"{location}.permissions must be a list of strings"))

    if "inputs" in tool:
        errors.extend(_validate_param_block(tool["inputs"], location, manifest_path, block_name="inputs"))

    if "outputs" in tool:
        errors.extend(_validate_param_block(tool["outputs"], location, manifest_path, block_name="outputs", require_required=False))

    if "runtime" in tool and not isinstance(tool["runtime"], dict):
        errors.append(ValidationIssue(manifest_path, f"{location}.runtime must be an object when provided"))
    elif isinstance(tool.get("runtime"), dict):
        runtime = tool["runtime"]
        if "timeout_seconds" in runtime and not _is_positive_number(runtime["timeout_seconds"]):
            errors.append(ValidationIssue(manifest_path, f"{location}.runtime.timeout_seconds must be a positive number"))
        if "concurrency" in runtime and not isinstance(runtime["concurrency"], str):
            errors.append(ValidationIssue(manifest_path, f"{location}.runtime.concurrency must be a string"))

    return errors


def _validate_module(module_path: str, class_name: Optional[str], repo_root: Path) -> Optional[str]:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        return f"module import failed ({exc})"

    if class_name:
        if not hasattr(module, class_name):
            return f"class_name '{class_name}' not found in module"
        attr = getattr(module, class_name)
        if not isinstance(attr, type) or not issubclass(attr, Tool):
            return f"class_name '{class_name}' must inherit from Tool"
        return None

    tool_classes = [cls for cls in module.__dict__.values() if isinstance(cls, type) and issubclass(cls, Tool) and cls is not Tool]
    if not tool_classes:
        return "no Tool subclass found in module"
    return None


def _validate_param_block(
    block: Any,
    location: str,
    manifest_path: Path,
    block_name: str,
    require_required: bool = True,
) -> Iterable[ValidationIssue]:
    errors: List[ValidationIssue] = []
    if not isinstance(block, dict):
        errors.append(ValidationIssue(manifest_path, f"{location}.{block_name} must be an object"))
        return errors

    for param_name, spec in block.items():
        param_path = f"{location}.{block_name}.{param_name}"
        if not isinstance(spec, dict):
            errors.append(ValidationIssue(manifest_path, f"{param_path} must be an object"))
            continue
        param_type = spec.get("type")
        if not isinstance(param_type, str) or param_type not in PRIMITIVE_TYPES:
            errors.append(ValidationIssue(manifest_path, f"{param_path}.type must be one of {sorted(PRIMITIVE_TYPES)}"))
        if require_required and "required" in spec and not isinstance(spec["required"], bool):
            errors.append(ValidationIssue(manifest_path, f"{param_path}.required must be a boolean when provided"))
    return errors


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    repo_root = args.root.resolve()

    manifest_paths = args.manifests or [Path("config/tool_manifest.json")]
    manifest_paths = [path if path.is_absolute() else repo_root / path for path in manifest_paths]

    issues: List[ValidationIssue] = []
    for manifest_path in manifest_paths:
        data = load_manifest(manifest_path)
        issues.extend(validate_manifest(data, manifest_path.resolve(), repo_root))

    if issues:
        print("Validation failed:")
        for issue in issues:
            try:
                rel_path = issue.path.relative_to(repo_root)
            except ValueError:
                rel_path = issue.path
            print(f" - {rel_path} :: {issue.message}")
        return 1

    print(f"Validated {len(manifest_paths)} manifest file(s) with no issues.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
