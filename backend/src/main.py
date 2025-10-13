from fastapi import FastAPI, WebSocket
from api.websocket.connection import handle_client_connection

app = FastAPI(
    title="Interactive Agent Chat System",
    description="WebSocket-based chat system with multi-channel feedback support",
    version="1.0.0"
)

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for chat sessions."""
    await handle_client_connection(websocket, user_id)

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}