"""
ws_handler.py — FastAPI WebSocket Real-Time Conversational Handler

WHAT IT DOES:
Manages real-time, bidirectional communication between the user and 
the AI. It allows for a "live chat" experience where text tokens 
stream in as they are generated, and audio is processed instantly.

WHY IT EXISTS:
WebSockets provide much lower latency than traditional HTTP requests. 
This is crucial for voice interaction to feel natural—allowing the 
assistant to start responding while the user is still waiting.

CONNECTIONS:
- Registered as a route in 'app.main'.
- Coordinates between 'app.voice.stt', 'app.llm.response_generator', 
  and 'app.voice.tts' in a streaming fashion.
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.logger import logger

router = APIRouter()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    Real-time streaming conversational WebSocket endpoint.

    Farmers connect here for live voice+text conversation.
    Supports:
    - Streaming text responses (token by token)
    - Audio input (base64-encoded audio → STT → RAG → TTS)
    - Ping/pong for connection keep-alive

    Args:
        session_id: Unique session identifier.
                    Use "new" to auto-create a session.
    """
    from app.main import session_manager, response_generator

    # Accept the WebSocket connection
    await websocket.accept()

    # Auto-create session if "new" is passed as session_id
    if session_id == "new":
        session_id = session_manager.new_session()
        await _send(websocket, {
            "type": "session_created",
            "session_id": session_id,
            "message": "ನಮಸ್ಕಾರ! ಕೃಷಿ ಮಿತ್ರಕ್ಕೆ ಸ್ವಾಗತ. ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
        })
    elif not session_manager.session_exists(session_id):
        # Session expired → recreate silently
        session_manager.memory.create_session(session_id)

    logger.info(
        "WebSocket connected | session={id}", id=session_id[:8]
    )

    try:
        while True:
            # Wait for a message from the client
            raw = await websocket.receive_text()

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_error(websocket, "Invalid JSON message format")
                continue

            msg_type = msg.get("type", "text")

            # ── Ping / keep-alive ─────────────────────────────────────────────
            if msg_type == "ping":
                await _send(websocket, {"type": "pong"})
                continue

            # ── Text message ──────────────────────────────────────────────────
            elif msg_type == "text":
                user_text = msg.get("content", "").strip()
                if not user_text:
                    await _send_error(websocket, "Empty message received")
                    continue

                logger.info(
                    "WS text | session={id} | text={t}",
                    id=session_id[:8], t=user_text[:60]
                )

                # Stream response tokens back to client
                await _stream_response(
                    websocket=websocket,
                    session_id=session_id,
                    user_query=user_text,
                    response_generator=response_generator,
                )


            else:
                await _send_error(websocket, f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected | session={id}", id=session_id[:8]
        )
    except Exception as e:
        logger.error(
            "WebSocket error | session={id} | error={e}",
            id=session_id[:8], e=e
        )
        try:
            await _send_error(websocket, f"Server error: {str(e)}")
        except Exception:
            pass


# ── Helper Functions ──────────────────────────────────────────────────────────

async def _stream_response(
    websocket: WebSocket,
    session_id: str,
    user_query: str,
    response_generator,
):
    """
    Stream the assistant's response token-by-token over WebSocket.

    Also optionally synthesizes audio and sends it at the end.

    Args:
        websocket:        Active WebSocket connection
        session_id:       Current session ID
        user_query:       The farmer's text query
        response_generator: ResponseGenerator instance
    """
    await _send(websocket, {"type": "status", "content": "generating"})

    full_response = []
    try:
        async for token in response_generator.generate_stream(session_id, user_query):
            if token == getattr(response_generator, "_DB_MATCH_SENTINEL", None):
                continue
            full_response.append(token)
            # Send each token immediately for real-time streaming effect
            await _send(websocket, {
                "type": "token",
                "content": token,
            })
    except Exception as e:
        logger.error("Stream error: {e}", e=e)
        await _send_error(websocket, f"Generation error: {str(e)}")
        return

    complete_text = "".join(full_response)

    # Send the complete response as a "done" message
    await _send(websocket, {
        "type": "response",
        "content": complete_text,
        "session_id": session_id,
        "done": True,
    })




async def _send(websocket: WebSocket, data: dict):
    """Send a JSON message to the WebSocket client."""
    await websocket.send_text(json.dumps(data, ensure_ascii=False))


async def _send_error(websocket: WebSocket, message: str):
    """Send an error message to the WebSocket client."""
    await _send(websocket, {"type": "error", "content": message})
