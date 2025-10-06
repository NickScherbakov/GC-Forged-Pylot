# GC-Forged-Pylot

> **[Visit our landing page](https://nickscherbakov.github.io/GC-Forged-Pylot/)** for a visual introduction to the project.

**GC-Forged-Pylot** is an autonomous 24/7 coding system built on [llama.cpp](https://github.com/ggerganov/llama.cpp) with integrated GitHub Copilot functionality. It runs a local LLM server that provides an OpenAI-compatible API, supports chat and text completion endpoints, and allows for real-time streaming via WebSockets.

## Features

- **Local LLM Server:** Launch a local server using FastAPI that wraps a llama.cpp model.
- **API Endpoints:** Offers endpoints for status, completions, chat completions, and configuration.
- **Streaming Support:** Provides streaming responses for real-time data through HTTP and WebSocket protocols.
- **Caching:** Uses an in-memory cache to speed up repeated requests.
- **Environment Configurable:** Loads configuration from a JSON file and environment variables.
- **Hardware Optimization:** Automatically detects hardware capabilities and optimizes LLM parameters.
- **Self-Improvement:** Features a continuous learning loop that allows the system to refine itself.
- **Autonomous Operation:** Can run in autonomous mode, completing tasks with minimal human input.

## Advanced Capabilities

### Hardware Optimization System

GC-Forged-Pylot includes a sophisticated hardware optimization system that:

- **Auto-detects hardware** - Identifies CPU, RAM, and GPU specifications
- **Optimizes compilation** - Selects optimal flags for compiling llama.cpp
- **Tunes runtime parameters** - Determines optimal thread count, context size, batch size, and GPU layers
- **Benchmarks performance** - Tests various configurations to find the optimal setup
- **Persists profiles** - Saves hardware profiles for subsequent launches
- **Mock benchmarking** - Can run simulated benchmarks on systems without development tools

```bash
# Optimize hardware settings and parameters
python optimize_llama.py --benchmark --model ./models/your-model.gguf

# Skip compilation on systems without development tools
python optimize_llama.py --benchmark --skip-compilation --model ./models/your-model.gguf
```

### Self-Improvement System

The system includes a self-improvement mechanism that allows it to:

- **Analyze tasks** - Determine required capabilities for task completion
- **Generate code** - Create new modules to address missing functionality
- **Evaluate results** - Assess the quality of its own outputs
- **Learn from feedback** - Process user feedback to improve future performance
- **Autonomous cycles** - Run continuous improvement loops until reaching confidence threshold

```bash
# Execute a task with self-improvement cycles
python run_autonomous.py "Your task description" --cycles 5 --threshold 0.9

# Run in continuous self-improvement mode
python run_autonomous.py "Your task description" --continuous
```

## Emerging Applications

Beyond the core server, GC-Forged-Pylot is already proving useful in several less-obvious domains:

- **Autonomous SecOps Sentry** – ingest on-prem log streams, surface anomalies, and ship remediation patches without leaking telemetry to the cloud.
- **Edge & Robotics Operator** – pair hardware-aware optimization with Jetson/ARM builds to keep fleets of offline devices updated and self-healing.
- **Private LLM R&D Lab** – spin up isolated sandboxes to benchmark prompts, models, and runtime tweaks while the memory system curates experiment history.
- **Academic Autonomy Studio** – let learners launch guided self-improvement cycles, inspect planner/executor traces, and defend their findings with reproducible logs.

If you explore a new scenario, open a discussion or PR so we can amplify it in the docs.

## Community Onboarding & Growth

We want the next hundred contributors to hit the ground running. A few initiatives you can join or kick off:

- **Self-Improvement Gallery** – publish your best task cycles (plans, diffs, metrics) so others can fork and rerun them locally. Get inspired by [Case Study 001](docs/case-studies/self-improvement-cycle-001.md) and [Case Study 002](docs/case-studies/self-improvement-cycle-002.md); validate your artifacts with `python bin/validate_gallery.py`.
- **Extension Marketplace** – build and share tool manifests hooked into `src/bridge/tool_manager.py` for DevOps, data, or creative workflows; start with the [Tool Manifest Specification](docs/specs/tool_manifest.md), drop JSON or YAML bundles in `config/`, and lint them with `python bin/validate_tool_manifest.py`.
- **Telemetry Dashboard** – prototype visualizers for planner/executor traces and share insights on performance bottlenecks using the [Telemetry Event Specification](docs/specs/telemetry_events.md).
- **Dual-Agent Reviews** – experiment with two coordinated agents (builder + reviewer) and document the patterns that work best; align with the [Dual-Agent Collaboration Protocol](docs/specs/dual_agent_protocol.md).
- **Model Optimization Recipes** – automate GGUF conversions, benchmarking, and tuning scripts so new users can contribute quickly on their hardware.

Jump into the [Discussions](https://github.com/NickScherbakov/GC-Forged-Pylot/discussions) tab or file an issue with your proposal—we are happy to collaborate and highlight community-led efforts. For a high-level view of where we are heading, check the [GC-Forged-Pylot Roadmap 2025](docs/ROADMAP_2025.md).

## Project Structure

```
GC-Forged-Pylot/
├── main.py                # Entry point for the LLM server
├── optimize_llama.py      # Hardware optimization script
├── run_autonomous.py      # Autonomous agent runner with self-improvement
├── setup.py               # Package setup script and dependencies
├── config/                # Configuration files
│   ├── agent_config.json  # Agent configuration
│   ├── hardware_profile.json # Hardware optimization profile
├── src/
│   ├── core/
│   │   ├── hardware_optimizer.py # Hardware detection and optimization
│   │   ├── server.py      # Server implementation and API endpoints
│   │   ├── ...            # Other core modules
│   ├── self_improvement.py # Self-improvement and continuous learning module
│   ├── bridge/            # Bridges to external systems and tools
│   └── pylot-agent/       # Autonomous agent implementation
└── tests/
    └── core/              # Test modules
```

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/gc-forged-pylot.git
   cd gc-forged-pylot
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt  # or use setup.py by running: pip install -e .
   ```

4. **Set up environment variables:**

   Create a `.env` file in the project root with required environment variables (e.g. `GC_MODEL_PATH`).

## Running the Server

Run the server by executing the entry point:

```bash
python main.py --config config.json --host 127.0.0.1 --port 8000 --reload
```

The server uses [uvicorn](https://www.uvicorn.org/) to serve the FastAPI application. You should see logs indicating the model is being loaded and the server is running at the specified host and port.

## API Endpoints

The server provides several endpoints:

- `GET /v1/status`  
  Returns server status, including uptime, model info, active connections, and cache statistics.

- `GET /v1/models`  
  Lists available models.

- `POST /v1/completions`  
  Generates text completions for the given prompt. Supports optional streaming if requested.

- `POST /v1/chat/completions`  
  Processes chat completions based on an array of messages.

- **WebSocket Endpoint:**  
  `ws://<host>:<port>/ws/completions` for streaming completions and chat in real time.

- `GET /v1/config` and `POST /v1/config`  
  Retrieve and update the current server configuration.

For more details on request payloads and responses, check the API models defined in [server.py](e:\GC-Forged-Pylot\src\core\server.py).

## Development & Testing

- **Run Tests:**  
  Use your preferred test runner (e.g. pytest) to run tests located in the `tests/` folder.

  ```bash
  pytest
  ```

- **Auto-reload:**  
  Use the `--reload` flag when starting the server for automatic code reloading during development.

## Contributing

Contributions are welcome. Please submit pull requests or open issues to help improve the project.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Inspired by [llama.cpp](https://github.com/ggerganov/llama.cpp) and GitHub Copilot.
- Built by the GC-Forged-Pylot Team.
