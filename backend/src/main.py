from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .api.websocket.connection import handle_client_connection
from .api.routers import auth
from .api.routers import chat
from .config import settings

app = FastAPI(
    title="Interactive Agent Chat System",
    description="WebSocket-based chat system with multi-channel feedback support",
    version="1.0.0",
    debug=settings.debug
)

# CORS Configuration - Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Alternative frontend port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for chat sessions."""
    await handle_client_connection(websocket, user_id)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Interactive Agent Chat System API",
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": "1.0.0"
    }