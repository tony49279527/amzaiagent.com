from fastapi import WebSocket
from typing import Dict, List
import asyncio
import json

class ProgressManager:
    def __init__(self):
        # Store active connections: task_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store message history: task_id -> list of messages
        self.message_history: Dict[str, List[dict]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        print(f"WS: Client connected to task {task_id}")
        
        # Replay history to new client
        if task_id in self.message_history:
            print(f"WS: Replaying {len(self.message_history[task_id])} messages for {task_id}")
            for msg in self.message_history[task_id]:
                try:
                    await websocket.send_json(msg)
                except Exception as e:
                    print(f"WS Replay Error: {e}")
                    break

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
                # Optional: Clear history when no clients left? 
                # Better to keep it for a bit or clear on task completion (handled elsewhere or expire).
                # For now, we'll keep it to support refresh, but maybe cap size?
        print(f"WS: Client disconnected from task {task_id}")

    async def emit(self, task_id: str, step: str, status: str, progress: int, details: dict = None):
        """
        Send a progress update to all clients watching this task.
        """
        if task_id not in self.active_connections:
            return

        message = {
            "task_id": task_id,
            "step": step,           # e.g., "Web Research"
            "status": status,       # e.g., "Scraping YouTube..."
            "progress": progress,   # 0-100
            "details": details or {} # Extra data like logs or JSON previews
        }

        # Store in history
        if task_id not in self.message_history:
            self.message_history[task_id] = []
        self.message_history[task_id].append(message)


        # Broadcast to all connected clients
        to_remove = []
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception:
                to_remove.append(connection)
        
        # Cleanup dead connections
        for dead in to_remove:
            self.disconnect(task_id, dead)

# Global instance
progress_manager = ProgressManager()
