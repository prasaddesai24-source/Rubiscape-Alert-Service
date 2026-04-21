"""
WebSocket routes — real-time alert push to connected browser clients.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    Browser dashboard connects here to receive live alert push notifications.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — wait for any client message (ping/pong)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected cleanly")
    except Exception as e:
        manager.disconnect(websocket)
        logger.warning(f"WebSocket error: {e}")
