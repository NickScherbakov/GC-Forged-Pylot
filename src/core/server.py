"""
Core server implementation that interfaces with llama.cpp.
"""
import os
import sys
import json
import asyncio
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union, Callable

# FastAPI imports
try:
    from fastapi import FastAPI, Request, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
    from fastapi.responses import StreamingResponse
    import uvicorn
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .llm_llama_cpp import LLamaLLM, LLAMA_CPP_AVAILABLE
from .llm_interface import LLMResponse

# Корректный импорт класса из llm_external.py
from .llm_external import ExternalLLMAdapter

logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelCache:
    """
    Кэш для результатов генерации LLM для повторного использования.
    """
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Инициализирует кэш модели.
        
        Args:
            max_size: Максимальное количество элементов в кэше
            ttl: Время жизни записи в кэше в секундах
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def get_key(self, prompt: str, **params) -> str:
        """
        Генерирует ключ для кэширования на основе промпта и параметров.
        
        Args:
            prompt: Текстовый промпт
            **params: Параметры генерации
            
        Returns:
            str: Уникальный ключ для кэширования
        """
        # Сортируем параметры для консистентного ключа
        param_str = json.dumps(params, sort_keys=True)
        return f"{prompt}:{param_str}"
    
    def get(self, key: str) -> Optional[Tuple[Any, float]]:
        """
        Получает значение из кэша.
        
        Args:
            key: Ключ для поиска
            
        Returns:
            Optional[Any]: Значение из кэша или None
        """
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp <= self.ttl:
                    self.hits += 1
                    return value
                else:
                    # Удаляем устаревшую запись
                    del self.cache[key]
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Добавляет значение в кэш.
        
        Args:
            key: Ключ
            value: Значение для кэширования
        """
        with self.lock:
            # Проверяем размер кэша
            if len(self.cache) >= self.max_size:
                # Удаляем самую старую запись
                oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
                del self.cache[oldest_key]
            
            self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Очищает кэш."""
        with self.lock:
            self.cache.clear()
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Получает статистику кэша.
        
        Returns:
            Dict[str, Any]: Статистика кэша
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "ttl": self.ttl
            }


class LlamaServer:
    """
    A wrapper around llama.cpp that provides enhanced functionality
    for IDE integration and continuous operation.
    """
    
    def __init__(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = 0, verbose: bool = False, cache_config: dict = None, api_keys: list = None):
        """
        Initialize the LlamaServer with model path and configuration.
        
        Args:
            model_path: Path to the GGUF model file
            config: Configuration dictionary or object
        """
        self.model_path = model_path or os.environ.get("GC_MODEL_PATH")
        self.config = {
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "verbose": verbose,
            **(cache_config or {}),
            **(api_keys or {})
        }
        self.running = False
        self.server_thread = None
        self.app = FastAPI(
            title="Local Llama Server",
            description="OpenAI-compatible API for local Llama models",
            version="0.1.0"
        )
        self._configure_routes()
        self._configure_middleware() # Add middleware configuration if needed
        self._llm_instance = None
        self._cache = ModelCache(
            max_size=self.config.get("cache_size", 100),
            ttl=self.config.get("cache_ttl", 3600)
        )
        self._active_connections = set()
        self._validate_setup()
        logger.info(f"LlamaServer initialized with model: {self.model_path}")
        
    def _validate_setup(self):
        """Ensure the server is properly configured."""
        if not self.model_path:
            logger.error("No model path provided")
            raise ValueError("Model path must be provided via argument or GC_MODEL_PATH env variable")
        
        if not Path(self.model_path).exists():
            logger.error(f"Model file not found: {self.model_path}")
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
    def _load_model(self):
        """Load the language model using llama-cpp-python."""
        try:
            # Ограничиваем использование памяти для модели на основе доступной системной памяти
            import psutil
            avail_memory = psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB
            logger.info(f"Available system memory: {avail_memory:.2f} GB")
            
            # Определяем конфигурацию для модели на основе доступной памяти
            model_config = self.config.copy()
            
            # Определяем тип квантизации на основе доступной памяти и настроек пользователя
            if avail_memory < 8 and not model_config.get("quantization_type"):
                logger.info("Low memory detected, using 4-bit quantization")
                model_config["quantization_type"] = "q4_0"
            
            # Создаем экземпляр LLamaLLM
            self._llm_instance = LLamaLLM({
                "model_path": self.model_path,
                "n_ctx": model_config.get("context_size", 4096),
                "n_threads": model_config.get("threads"),
                "n_gpu_layers": model_config.get("gpu_layers", -1 if model_config.get("use_gpu", True) else 0),
                "use_gpu": model_config.get("use_gpu", True),
                "gpu_backend": model_config.get("gpu_backend"),
                "gpu_device": model_config.get("gpu_device", 0),
                "seed": model_config.get("seed", 42),
                "verbose": model_config.get("verbose", False),
                "use_mlock": model_config.get("use_mlock", True),
                "use_mmap": model_config.get("use_mmap", True),
                "rope_scaling_type": model_config.get("rope_scaling_type"),
                "rope_scaling_factor": model_config.get("rope_scaling_factor", 1.0)
            })
            
            logger.info("Model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
        
    def _configure_routes(self):
        # Определяем модели для API если доступен FastAPI
        if FASTAPI_AVAILABLE:
            # Создаем модели данных
            class CompletionRequest(BaseModel):
                prompt: str
                max_tokens: int = Field(default=256)
                temperature: float = Field(default=0.7, ge=0.0, le=1.0)
                top_p: float = Field(default=0.95, ge=0.0, le=1.0)
                top_k: int = Field(default=40, ge=0)
                repeat_penalty: float = Field(default=1.1, ge=0.0)
                stream: bool = Field(default=False)
                stop: List[str] = Field(default=[])
                
            class ChatMessage(BaseModel):
                role: str
                content: str

            class ChatRequest(BaseModel):
                messages: List[ChatMessage]
                max_tokens: int = Field(default=256)
                temperature: float = Field(default=0.7, ge=0.0, le=1.0)
                top_p: float = Field(default=0.95, ge=0.0, le=1.0)
                top_k: int = Field(default=40, ge=0)
                repeat_penalty: float = Field(default=1.1, ge=0.0)
                stream: bool = Field(default=False)
                stop: List[str] = Field(default=[])
            
            class ModelConfig(BaseModel):
                key: str
                value: Any
            
            # Состояние для хранения начального времени сервера
            self._start_time = time.time()
            
            # API-эндпоинты
            @self.app.get("/v1/status")
            async def get_status():
                """Get the server status."""
                cache_stats = self._cache.get_stats()
                
                return {
                    "status": "running" if self._llm_instance else "not_ready",
                    "model": os.path.basename(self.model_path) if self.model_path else None,
                    "uptime": time.time() - self._start_time,
                    "connections": len(self._active_connections),
                    "cache": cache_stats
                }
                
            @self.app.get("/v1/models")
            async def list_models():
                """List available models."""
                model_name = os.path.basename(self.model_path) if self.model_path else "unknown"
                
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": "local-" + model_name,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "local",
                            "permissions": [],
                            "root": model_name,
                            "parent": None
                        }
                    ]
                }
                
            @self.app.post("/v1/completions")
            async def create_completion(request: CompletionRequest):
                """Create a completion for the given prompt."""
                if not self._llm_instance:
                    raise HTTPException(status_code=503, detail="Model not loaded")
                    
                # Проверяем кэш, если не потоковый запрос
                if not request.stream:
                    cache_key = self._cache.get_key(
                        request.prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k,
                        repeat_penalty=request.repeat_penalty,
                        stop=request.stop
                    )
                    cached_result = self._cache.get(cache_key)
                    
                    if cached_result:
                        logger.debug("Cache hit for completion")
                        return cached_result
                
                # Если потоковый запрос
                if request.stream:
                    return StreamingResponse(
                        self._streaming_completion(request),
                        media_type="text/event-stream"
                    )
                    
                # Выполняем генерацию
                try:
                    llm_response = self._llm_instance.generate(
                        request.prompt,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k,
                        repeat_penalty=request.repeat_penalty,
                        stop=request.stop
                    )
                    
                    # Формируем ответ в формате OpenAI API
                    response = {
                        "id": f"cmpl-{uuid.uuid4()}",
                        "object": "text_completion",
                        "created": int(time.time()),
                        "model": os.path.basename(self.model_path),
                        "choices": [
                            {
                                "text": llm_response.text,
                                "index": 0,
                                "logprobs": None,
                                "finish_reason": llm_response.metadata.get("finish_reason", "length")
                            }
                        ],
                        "usage": {
                            "prompt_tokens": self._llm_instance.count_tokens(request.prompt),
                            "completion_tokens": self._llm_instance.count_tokens(llm_response.text),
                            "total_tokens": llm_response.metadata.get("tokens_used", 0)
                        }
                    }
                    
                    # Кэшируем результат
                    self._cache.set(cache_key, response)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Error generating completion: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                
            @self.app.post("/v1/chat/completions")
            async def create_chat_completion(request: ChatRequest):
                """Create a chat completion."""
                if not self._llm_instance:
                    raise HTTPException(status_code=503, detail="Model not loaded")
                    
                # Преобразуем запрос в формат, понятный модели
                messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
                
                # Проверяем кэш, если не потоковый запрос
                if not request.stream:
                    cache_key = self._cache.get_key(
                        json.dumps(messages),
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k,
                        repeat_penalty=request.repeat_penalty,
                        stop=request.stop
                    )
                    cached_result = self._cache.get(cache_key)
                    
                    if cached_result:
                        logger.debug("Cache hit for chat completion")
                        return cached_result
                
                # Если потоковый запрос
                if request.stream:
                    return StreamingResponse(
                        self._streaming_chat(request, messages),
                        media_type="text/event-stream"
                    )
                    
                # Выполняем генерацию
                try:
                    llm_response = self._llm_instance.chat(
                        messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k,
                        repeat_penalty=request.repeat_penalty,
                        stop=request.stop
                    )
                    
                    # Формируем ответ в формате OpenAI API
                    response = {
                        "id": f"chatcmpl-{uuid.uuid4()}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": os.path.basename(self.model_path),
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": llm_response.text
                                },
                                "index": 0,
                                "finish_reason": llm_response.metadata.get("finish_reason", "stop")
                            }
                        ],
                        "usage": {
                            "prompt_tokens": sum(self._llm_instance.count_tokens(msg["content"]) for msg in messages),
                            "completion_tokens": self._llm_instance.count_tokens(llm_response.text),
                            "total_tokens": llm_response.metadata.get("tokens_used", 0)
                        }
                    }
                    
                    # Кэшируем результат
                    self._cache.set(cache_key, response)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Error generating chat completion: {e}")
                    raise HTTPException(status_code=500, detail=str(e))
                
            @self.app.websocket("/ws/completions")
            async def websocket_endpoint(websocket: WebSocket):
                """WebSocket endpoint for streaming completions."""
                await websocket.accept()
                self._active_connections.add(websocket)
                
                try:
                    while True:
                        data = await websocket.receive_json()
                        
                        # Проверяем тип запроса
                        if data.get("type") == "completion":
                            # Создаем задачу для выполнения генерации
                            asyncio.create_task(self._handle_ws_completion(websocket, data))
                        elif data.get("type") == "chat":
                            # Создаем задачу для выполнения чата
                            asyncio.create_task(self._handle_ws_chat(websocket, data))
                        else:
                            await websocket.send_json({"error": "Unknown request type"})
                            
                except WebSocketDisconnect:
                    logger.debug("WebSocket client disconnected")
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                finally:
                    self._active_connections.remove(websocket)
                    
            async def _handle_ws_completion(self, websocket: WebSocket, data: Dict[str, Any]):
                """Handle WebSocket completion request."""
                try:
                    generator = self._llm_instance.generate(
                        data.get("prompt", ""),
                        max_tokens=data.get("max_tokens", 256),
                        temperature=data.get("temperature", 0.7),
                        top_p=data.get("top_p", 0.95),
                        top_k=data.get("top_k", 40),
                        repeat_penalty=data.get("repeat_penalty", 1.1),
                        stop=data.get("stop", []),
                        stream=True
                    )
                    
                    completion_id = f"wscomp-{uuid.uuid4()}"
                    
                    for chunk in generator:
                        await websocket.send_json({
                            "id": completion_id,
                            "type": "completion_chunk",
                            "text": chunk.text,
                            "finish_reason": chunk.metadata.get("finish_reason")
                        })
                        
                        if chunk.metadata.get("finish_reason"):
                            break
                            
                    await websocket.send_json({
                        "id": completion_id,
                        "type": "completion_finished"
                    })
                    
                except Exception as e:
                    logger.error(f"Error in WebSocket completion: {e}")
                    await websocket.send_json({"error": str(e)})
                    
            async def _handle_ws_chat(self, websocket: WebSocket, data: Dict[str, Any]):
                """Handle WebSocket chat request."""
                try:
                    messages = data.get("messages", [])
                    generator = self._llm_instance.chat(
                        messages,
                        max_tokens=data.get("max_tokens", 256),
                        temperature=data.get("temperature", 0.7),
                        top_p=data.get("top_p", 0.95),
                        top_k=data.get("top_k", 40),
                        repeat_penalty=data.get("repeat_penalty", 1.1),
                        stop=data.get("stop", []),
                        stream=True
                    )
                    
                    chat_id = f"wschat-{uuid.uuid4()}"
                    
                    for i, chunk in enumerate(generator):
                        await websocket.send_json({
                            "id": chat_id,
                            "type": "chat_chunk",
                            "role": "assistant" if i == 0 else "",
                            "content": chunk.text,
                            "finish_reason": chunk.metadata.get("finish_reason")
                        })
                        
                        if chunk.metadata.get("finish_reason"):
                            break
                            
                    await websocket.send_json({
                        "id": chat_id,
                        "type": "chat_finished"
                    })
                    
                except Exception as e:
                    logger.error(f"Error in WebSocket chat: {e}")
                    await websocket.send_json({"error": str(e)})
                    
            @self.app.get("/v1/config")
            async def get_config():
                """Get current server configuration."""
                # Возвращаем безопасную копию конфига без чувствительной информации
                safe_config = {k: v for k, v in self.config.items() if k not in ["api_key", "secret"]}
                return {"config": safe_config}
                
            @self.app.post("/v1/config")
            async def update_config(config: Dict[str, Any]):
                """Update server configuration."""
                # Обновляем конфигурацию
                for key, value in config.items():
                    self.config[key] = value
                    
                # Если конфигурация модели изменена, нужна перезагрузка
                model_config_keys = ["n_ctx", "n_threads", "n_gpu_layers", "use_gpu"]
                if any(key in model_config_keys for key in config.keys()):
                    logger.info("Model configuration changed, reload required")
                    
                return {"status": "success", "config": {k: v for k, v in self.config.items() if k not in ["api_key", "secret"]}}
                
        # Готово, возвращаем True
        logger.info("API endpoints configured successfully")
        return True

    def _configure_middleware(self):
        # Example: Add CORS middleware if needed
        # from fastapi.middleware.cors import CORSMiddleware
        # origins = ["*"] # Adjust as needed
        # self.app.add_middleware(
        #     CORSMiddleware,
        #     allow_origins=origins,
        #     allow_credentials=True,
        #     allow_methods=["*"],
        #     allow_headers=["*"],
        # )
        pass # Add other middleware if necessary

    def get_app(self):
        """Returns the FastAPI application instance."""
        return self.app

    def start(self, host="0.0.0.0", port=8080):
        """Start the LlamaServer on the specified host and port."""
        if self.running:
            logger.warning("Server is already running")
            return False
            
        # Load the model
        if not self._load_model():
            return False
            
        # Set up the API
        if not FASTAPI_AVAILABLE:
            logger.error("FastAPI not available. Cannot start server.")
            return False
            
        if not self._setup_api():
            return False
            
        # Start the server
        self.running = True
        self._start_time = time.time()
        
        # Start in a separate thread
        self.server_thread = threading.Thread(
            target=self._server_loop,
            args=(host, port),
            daemon=True
        )
        self.server_thread.start()
        
        logger.info(f"LlamaServer running on http://{host}:{port}")
        return True
        
    def _server_loop(self, host, port):
        """Main server loop."""
        try:
            # Запускаем uvicorn с настроенным приложением FastAPI
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False
            
    def stop(self):
        """Stop the LlamaServer."""
        if not self.running:
            logger.warning("Server is not running")
            return
            
        logger.info("Stopping LlamaServer")
        self.running = False
        
        # Close all active WebSocket connections
        for connection in list(self._active_connections):
            try:
                # В асинхронном контексте нужно бы использовать
                # await connection.close()
                # но мы в синхронном методе, поэтому просто освобождаем ресурс
                self._active_connections.remove(connection)
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
        
        # Shutdown the server thread
        if self.server_thread:
            self.server_thread.join(timeout=5.0)
            
        # Clean up llama instance
        if self._llm_instance:
            self._llm_instance.shutdown()
            self._llm_instance = None
            
        logger.info("Server stopped")
        
    def generate(self, prompt, max_tokens=256, temperature=0.7, top_p=0.95, stream=False, **kwargs):
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stream: Whether to stream the results
            **kwargs: Additional parameters
            
        Returns:
            Generated text or generator if streaming
        """
        if not self._llm_instance:
            logger.error("Model not loaded, call start() first")
            return None
            
        logger.debug(f"Generating with prompt: {prompt[:50]}...")
        
        try:
            # Проверяем кэш, если не потоковая генерация
            if not stream:
                cache_key = self._cache.get_key(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    **kwargs
                )
                cached_result = self._cache.get(cache_key)
                
                if cached_result:
                    logger.debug("Cache hit for direct generation")
                    return cached_result
            
            # Генерируем ответ через llama_instance
            response = self._llm_instance.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream,
                **kwargs
            )
            
            # Если не потоковая генерация, кэшируем результат
            if not stream:
                self._cache.set(cache_key, response.text)
                return response.text
            else:
                # Для потоковой генерации возвращаем генератор
                return response
                
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None

    async def _streaming_completion(self, request):
        """Stream completions."""
        try:
            generator = self._llm_instance.generate(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                repeat_penalty=request.repeat_penalty,
                stop=request.stop,
                stream=True
            )
            
            completion_id = f"cmpl-{uuid.uuid4()}"
            created = int(time.time())
            
            for chunk in generator:
                data = {
                    "id": completion_id,
                    "object": "text_completion",
                    "created": created,
                    "model": os.path.basename(self.model_path),
                    "choices": [
                        {
                            "text": chunk.text,
                            "index": 0,
                            "logprobs": None,
                            "finish_reason": chunk.metadata.get("finish_reason", None)
                        }
                    ]
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
                if chunk.metadata.get("finish_reason"):
                    break
                    
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
            
    async def _streaming_chat(self, request, messages: List[Dict[str, str]]):
        """Stream chat completions."""
        try:
            generator = self._llm_instance.chat(
                messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                top_k=request.top_k,
                repeat_penalty=request.repeat_penalty,
                stop=request.stop,
                stream=True
            )
            
            completion_id = f"chatcmpl-{uuid.uuid4()}"
            created = int(time.time())
            
            for i, chunk in enumerate(generator):
                data = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": os.path.basename(self.model_path),
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant" if i == 0 else "",
                                "content": chunk.text
                            },
                            "finish_reason": chunk.metadata.get("finish_reason", None)
                        }
                    ]
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
                if chunk.metadata.get("finish_reason"):
                    break
                    
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

from flask import Flask, request, jsonify
from .llm_llama_cpp import LLamaLLM
from .llm_external import ExternalLLMAdapter  # Использовать правильный класс

app = Flask(__name__)

llama_model_path = "dummy_model_check.gguf"
external_api_url = "https://api.example.com/generate"

llama_model = LLamaLLM({"model_path": llama_model_path})
external_llm = ExternalLLMAdapter({"external_api": {"url": external_api_url}})  # Правильная инициализация

@app.route('/generate', methods=['POST'])
def generate_text():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        response = llama_model.generate(prompt)
        return jsonify({"text": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/external_generate', methods=['POST'])
def external_generate_text():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        response = external_llm.generate(prompt)  # Вызываем правильный метод
        return jsonify({"text": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)