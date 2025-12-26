from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from database import SessionLocal
import models
import json
import asyncio

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # project_id -> list of websockets
        self.user_connections: Dict[int, WebSocket] = {}  # user_id -> websocket
    
    async def connect(self, websocket: WebSocket, project_id: int, user_id: int):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        self.user_connections[user_id] = websocket
    
    def disconnect(self, websocket: WebSocket, project_id: int, user_id: int):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_project(self, message: dict, project_id: int, exclude_user_id: int = None):
        if project_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[project_id]:
                try:
                    # Skip the sender
                    if exclude_user_id and connection in self.user_connections.values():
                        user_id = [uid for uid, ws in self.user_connections.items() if ws == connection][0]
                        if user_id == exclude_user_id:
                            continue
                    await connection.send_json(message)
                except Exception as e:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                if project_id in self.active_connections:
                    self.active_connections[project_id] = [
                        c for c in self.active_connections[project_id] if c != conn
                    ]

manager = ConnectionManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int, user_id: int = 0):
    """WebSocket endpoint for real-time collaboration"""
    await manager.connect(websocket, project_id, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "connected",
                "message": "Connected to project",
                "project_id": project_id
            }),
            websocket
        )
        
        # Broadcast user joined
        await manager.broadcast_to_project(
            {
                "type": "user_joined",
                "user_id": user_id,
                "project_id": project_id
            },
            project_id,
            exclude_user_id=user_id
        )
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "file_edit":
                # Broadcast file edit to all other users
                await manager.broadcast_to_project(
                    {
                        "type": "file_edit",
                        "file_id": message.get("file_id"),
                        "file_path": message.get("file_path"),
                        "content": message.get("content"),
                        "user_id": user_id,
                        "project_id": project_id
                    },
                    project_id,
                    exclude_user_id=user_id
                )
            
            elif message_type == "cursor_move":
                # Broadcast cursor position
                await manager.broadcast_to_project(
                    {
                        "type": "cursor_move",
                        "file_id": message.get("file_id"),
                        "position": message.get("position"),
                        "user_id": user_id,
                        "project_id": project_id
                    },
                    project_id,
                    exclude_user_id=user_id
                )
            
            elif message_type == "chat_message":
                # Broadcast chat message
                await manager.broadcast_to_project(
                    {
                        "type": "chat_message",
                        "message": message.get("message"),
                        "user_id": user_id,
                        "project_id": project_id
                    },
                    project_id,
                    exclude_user_id=user_id
                )
            
            elif message_type == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id, user_id)
        # Broadcast user left
        await manager.broadcast_to_project(
            {
                "type": "user_left",
                "user_id": user_id,
                "project_id": project_id
            },
            project_id
        )

