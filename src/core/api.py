"""
REST API and WebSocket interfaces for the GC-Core server.
"""
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# --- Models for API requests and responses ---

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=256, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    stop: Optional[List[str]] = None
    stream: bool = False

class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    text: str
    finish_reason: Optional[str] = None
    usage: Dict[str, int]

# --- WebSocket connection manager ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_text(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# --- API implementation ---

class LlamaAPI:
    """
    API interface for the LlamaServer, providing HTTP and WebSocket endpoints.
    """
    
    def __init__(self, llama_server):
        """
        Initialize the API with a reference to the LlamaServer.
        
        Args:
            llama_server: Instance of LlamaServer
        """
        self.app = FastAPI(
            title="GC-Forged-Pylot API",
            description="API for interacting with the GC-Forged-Pylot LLM server",
            version="0.1.0"
        )
        self.llama_server = llama_server
        self.connection_manager = ConnectionManager()
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        logger.info("LlamaAPI initialized")
    
    def _register_routes(self):
        """Register HTTP and WebSocket routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint returning API status."""
            return {
                "status": "ok", 
                "version": "0.1.0",
                "model": self.llama_server.model_path
            }
        
        @self.app.post("/v1/completions")
        async def create_completion(req: CompletionRequest):
            """Generate completions for the provided prompt."""
            if not self.llama_server.running:
                raise HTTPException(status_code=503, detail="Server is not running")
            
            # Non-streaming response
            if not req.stream:
                start_time = time.time()
                text = self.llama_server.generate(
                    prompt=req.prompt,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                    top_p=req.top_p
                )
                
                # Calculate token counts (approximate)
                prompt_tokens = len(req.prompt.split())
                completion_tokens = len(text.split()) if text else 0
                
                return CompletionResponse(
                    id=f"cmpl-{int(time.time()*1000)}",
                    created=int(time.time()),
                    text=text or "",
                    finish_reason="stop",
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                )
            else:
                # Streaming responses should be handled by the /stream endpoint
                raise HTTPException(status_code=400, detail="Use WebSocket endpoint for streaming")
        
        @self.app.websocket("/v1/stream")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for streaming completions."""
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        req = CompletionRequest.parse_raw(data)
                        
                        # Set up streaming generation
                        for token in self.llama_server.generate(
                            prompt=req.prompt,
                            max_tokens=req.max_tokens,
                            temperature=req.temperature,
                            top_p=req.top_p,
                            stream=True
                        ):
                            response = {
                                "id": f"cmpl-{int(time.time()*1000)}",
                                "object": "text_completion",
                                "created": int(time.time()),
                                "text": token,
                                "finish_reason": None
                            }
                            await websocket.send_text(json.dumps(response))
                        
                        # Send completion message
                        await websocket.send_text(json.dumps({"finish_reason": "stop"}))
                        
                    except ValueError as e:
                        await websocket.send_text(json.dumps({"error": str(e)}))
                        
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy" if self.llama_server.running else "not_ready",
                "model": self.llama_server.model_path
            }