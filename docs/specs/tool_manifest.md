# Tool Manifest Specification

The tool manifest describes external executables, APIs, or scripts that GC-Forged-Pylot agents can invoke. A manifest lives alongside the repository (for example `config/tool_manifest.json` or `config/tool_manifest.yaml`) and is loaded by `ToolManager` during startup.

## Design Goals

1. **Declarative onboarding** – add a tool without modifying Python source.
2. **Safety-aware metadata** – capture permissions, audit notes, and expected inputs.
3. **Composable bundles** – allow grouping related tools into packages that can be shared.
4. **Versioned schema** – evolve the format while keeping backward compatibility.

## Top-Level Structure

Manifests may be expressed as JSON or YAML. The schema is identical; use whichever format best matches your workflow.

```jsonc
{
  "schema_version": "1.0",
  "metadata": {
    "name": "default",
    "description": "Core tool manifest bundled with GC-Forged-Pylot",
    "maintainers": ["your-handle"],
    "tags": ["core", "starter"]
  },
  "tools": [
    {
      "name": "git_status",
      "description": "Inspect repository status",
      "module": "src.bridge.tools.git_status",
      "class_name": "GitStatusTool",
      "permissions": ["read_repo"],
      "inputs": {
        "path": {
          "type": "string",
          "required": false,
          "default": "."
        },
        "short": {
          "type": "boolean",
          "required": false,
          "default": true
        }
      },
      "outputs": {
        "clean": {"type": "boolean"},
        "summary": {"type": "string"}
      },
      "runtime": {
        "timeout_seconds": 10,
        "concurrency": "serial"
      },
      "notes": "Shells out to git status"
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
| --- | --- | --- |
| `schema_version` | string | Semantic version of the manifest schema. Current: `1.0`. |
| `metadata` | object | Human-readable information about the manifest bundle. |
| `tools` | array | List of tool descriptors. |
| `tools[].name` | string | Unique identifier used when invoking the tool. |
| `tools[].description` | string | Short summary of what the tool does. |
| `tools[].module` | string | Python import path to the tool implementation. |

### Optional Fields

- `class_name`: Explicit class inside the module. When omitted, the first subclass of `Tool` is used.
- `permissions`: String list describing required capabilities (e.g., `read_repo`, `write_files`, `network`).
- `inputs` / `outputs`: Simple schemas to help the planner/reasoner reason about parameters. Types use JSON Schema primitives.
- `runtime`: Execution hints (timeouts, concurrency strategy, resource expectations).
- `notes`: Free-form guidance for human operators.

## Bundles & Overrides

Multiple manifests can be merged. Later entries override earlier ones when `name` matches. This allows organizations to:

- Ship a base manifest with the project.
- Layer local manifests for custom tooling or to disable risky tools.

## Validation Rules

1. Tool names must be lowercase, alphanumeric with `_` or `-`.
2. Module paths must be importable; they can be absolute (`src.bridge.tools.git_status`) or package-relative.
3. Permissions default to `[]` when unspecified.
4. Manifests with unknown `schema_version` should log a warning but attempt best-effort parsing.

## Future Extensions

- Support remote tool registries fetched over HTTPS.
- Sign manifests and verify integrity before loading.
- Add per-tool audit status (`experimental`, `trusted`).

## References

- `src/bridge/tool_manager.py` – runtime loader implementation.
- `config/tool_manifest.json` – default manifest shipped with the repository.
- `bin/validate_tool_manifest.py` – CLI validator that enforces the rules above.
