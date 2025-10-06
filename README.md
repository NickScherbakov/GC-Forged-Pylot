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

## 🤝 Contributing

We're building something revolutionary, and we'd love your help! Whether you're a student, researcher, or seasoned developer, there's a place for you here.

### 🎯 Quick Start for Contributors
- **New to open source?** Start with [Quick Wins](docs/QUICK_WINS.md) - easy tasks that make an impact
- **Want to contribute?** Read our [Contributing Guide](CONTRIBUTING.md) with gamified levels & achievements
- **Looking for ideas?** Check out [Innovative Features](docs/INNOVATIVE_FEATURES.md) for inspiration
- **Planning ahead?** See our [Roadmap](docs/ROADMAP.md) for upcoming features

### 🌟 Why Contribute?
- 🚀 Work with cutting-edge self-improving AI
- 🏆 Build your portfolio with innovative projects
- 🎓 Perfect for academic research and publications
- 💡 Influence the future of autonomous AI
- 🤝 Join a passionate community of builders

### 🎮 Contributor Levels
- 🥉 **Bronze**: First contribution merged
- 🥈 **Silver**: 5+ PRs, active community member
- 🥇 **Gold**: Core contributor, feature owner
- 💎 **Diamond**: Project champion, research leader

[Start your journey →](CONTRIBUTING.md)

Contributions are welcome. Please submit pull requests or open issues to help improve the project.

## License

This project is licensed under the [MIT License](LICENSE).

## 📚 Documentation

Explore our comprehensive documentation:

- 📖 [Innovative Features](docs/INNOVATIVE_FEATURES.md) - Non-obvious applications that make this project unique
- 🗺️ [Project Roadmap](docs/ROADMAP.md) - Our ambitious plan to revolutionize autonomous AI
- 🎯 [Quick Wins](docs/QUICK_WINS.md) - Easy first contributions for new members
- 💼 [Use Cases](docs/USE_CASES.md) - Real-world applications across industries
- 🤝 [Contributing Guide](CONTRIBUTING.md) - How to join our community
- 🔮 [Future Tasks](docs/FUTURE_TASKS.md) - Technical roadmap and priorities
- 🤖 [Self-Improvement](docs/SELF_IMPROVEMENT.md) - Deep dive into our core technology
- ⚡ [Autonomous Operation](docs/AUTONOMOUS_OPERATION.md) - 24/7 autonomous mode guide

## 🌟 Community & Support

- 💬 [GitHub Discussions](https://github.com/NickScherbakov/GC-Forged-Pylot/discussions) - Ask questions, share ideas
- 🐛 [Issue Tracker](https://github.com/NickScherbakov/GC-Forged-Pylot/issues) - Report bugs, request features
- 🎓 [Good First Issues](https://github.com/NickScherbakov/GC-Forged-Pylot/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) - Perfect for newcomers
- ⭐ Star us on GitHub - Show your support!

## Acknowledgments

- Inspired by [llama.cpp](https://github.com/ggerganov/llama.cpp) and GitHub Copilot.
- Built by the GC-Forged-Pylot Team and our amazing contributors.
