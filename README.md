# GC-Forged-Pylot

**GC-Forged-Pylot** is an autonomous 24/7 coding system built on [llama.cpp](https://github.com/ggerganov/llama.cpp) with integrated GitHub Copilot functionality. It runs a local LLM server that provides an OpenAI-compatible API, supports chat and text completion endpoints, and allows for real-time streaming via WebSockets.

## Features

- **Local LLM Server:** Launch a local server using FastAPI that wraps a llama.cpp model.
- **API Endpoints:** Offers endpoints for status, completions, chat completions, and configuration.
- **Streaming Support:** Provides streaming responses for real-time data through HTTP and WebSocket protocols.
- **Caching:** Uses an in-memory cache to speed up repeated requests.
- **Environment Configurable:** Loads configuration from a JSON file and environment variables.

## Project Structure

```
GC-Forged-Pylot/
├── main.py                # Entry point for the LLM server ([main.py](e:\GC-Forged-Pylot\main.py))
├── setup.py               # Package setup script and dependencies
├── src/
│   └── core/
│       ├── server.py      # Server implementation and API endpoints ([src/core/server.py](e:\GC-Forged-Pylot\src\core\server.py))
│       ├── ...            # Other modules (e.g. configuration, LLM interface)
└── tests/
    └── core/
         └── test_server_api.py  # API tests for the server
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
