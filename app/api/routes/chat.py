"""
chat.py — REST Chat API Route

WHAT IT DOES:
Provides standard text-based interaction endpoints. It handles creating 
new sessions, sending text messages to the AI, and retrieving 
conversation history.

WHY IT EXISTS:
This is the primary interface for text-based chatbots or web applications. 
It ensures that users who type in Kannada or English get the same 
high-quality, RAG-grounded advice as voice users.

CONNECTIONS:
- Uses 'app.main.session_manager' to track user history across turns.
- Uses 'app.main.response_generator' to run the RAG and LLM pipeline.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.config import settings
from app.api.routes.auth import require_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# ── Request / Response Models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """
    Request body for the chat endpoint.
    session_id is optional — if not provided, a new session is created.
    """
    session_id: str | None = Field(
        default=None,
        description="Existing session ID. Leave empty to start a new conversation."
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Farmer's text message in Kannada or English"
    )
    language: str = Field(
        default="kn",
        description="Preferred language for the response ('kn' or 'en')"
    )
    is_voice_mode: bool = Field(
        default=False,
        description="Whether this request is originating from Voice Mode"
    )


class ChatResponse(BaseModel):
    """Response body returned by the chat endpoint."""
    session_id: str
    response: str
    is_followup: bool = False
    context_used: bool = False
    retrieved_count: int = 0
    source: str = "llm"       # "database" | "rag" | "llm" | "followup"
    provider: str = "gemini"  # "database" | "gemini"
    message: str = "success"
    metadata: dict | None = None


class NewSessionResponse(BaseModel):
    """Response for new session creation."""
    session_id: str
    message: str = "New session created"


class HistoryResponse(BaseModel):
    """Response containing conversation history."""
    session_id: str
    history: list[dict]
    turn_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/sessions")
async def get_all_sessions(current_user: Dict[str, Any] = Depends(require_current_user)):
    """
    Get all persistent conversations belonging strictly to the authenticated user.
    """
    from app.main import session_manager
    user_id = current_user["id"]
    sessions_data = session_manager.conversation_manager.get_user_conversations(user_id)
    return {"sessions": sessions_data}


@router.post("/new", response_model=NewSessionResponse)
async def create_new_session(current_user: Dict[str, Any] = Depends(require_current_user)):
    """
    Create a new persistent conversation session owned by the authenticated user.
    """
    from app.main import session_manager
    user_id = current_user["id"]
    session_id = session_manager.new_session(user_id=user_id)
    logger.info("New persistent session created: {id} for user {uid}", id=session_id, uid=user_id)
    return NewSessionResponse(session_id=session_id)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(require_current_user)
):
    """
    Send a message and receive an agricultural AI response within the
    authenticated user's persistent conversation thread.
    """
    from app.main import session_manager, response_generator
    user_id = current_user["id"]

    # Validate session ownership or create a new user-owned conversation
    session_id = request.session_id
    if session_id:
        conv = session_manager.conversation_manager.get_conversation(user_id, session_id)
        if not conv:
            logger.info("Session {id} not found for user {uid}; creating fresh session", id=session_id, uid=user_id)
            session_id = session_manager.new_session(user_id=user_id)
    else:
        session_id = session_manager.new_session(user_id=user_id)

    # Ensure dialogue state and memory cache are hydrated for this user's session
    session_manager.ensure_session_loaded(session_id, user_id=user_id)

    try:
        result = await response_generator.generate(
            session_id=session_id,
            user_query=request.message,
            is_voice_mode=request.is_voice_mode,
            language=request.language,
            user_id=user_id,
        )
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            is_followup=result.get("is_followup", False),
            context_used=result.get("context_used", False),
            retrieved_count=result.get("retrieved_count", 0),
            source=result.get("source", "llm"),
            provider=result.get("provider", "gemini"),
            metadata=result.get("metadata", {}),
        )
    except Exception as e:
        logger.error("Chat error | session={id} | user={uid} | error={e}", id=session_id, uid=user_id, e=e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_current_user)
):
    """
    Retrieve the full conversation history for an authenticated user's session.
    Strictly verifies ownership to prevent unauthorized cross-user access.
    """
    from app.main import session_manager
    user_id = current_user["id"]

    conv = session_manager.conversation_manager.get_conversation(user_id, session_id)
    if not conv:
        logger.info("Session {id} history not found; returning empty history", id=session_id)
        return HistoryResponse(session_id=session_id, history=[], turn_count=0)

    # Make sure memory has it loaded if needed
    session_manager.ensure_session_loaded(session_id, user_id=user_id)
    history = session_manager.get_full_history(session_id, user_id=user_id)

    return HistoryResponse(
        session_id=session_id,
        history=history,
        turn_count=len(history) // 2,
    )


@router.delete("/session/{session_id}")
async def close_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(require_current_user)
):
    """
    Permanently delete a conversation thread and all its messages.
    Strictly verifies ownership so users cannot delete another user's conversation.
    """
    from app.main import session_manager
    user_id = current_user["id"]

    conv = session_manager.conversation_manager.get_conversation(user_id, session_id)
    if not conv:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{session_id}' not found"
        )

    session_manager.close_session(session_id, user_id=user_id)
    return {"status": "success", "message": f"Conversation {session_id} deleted successfully"}


@router.get("/sessions/count")
async def active_sessions(current_user: Dict[str, Any] = Depends(require_current_user)):
    """Return the number of conversations belonging to the current user."""
    from app.main import session_manager
    user_id = current_user["id"]
    user_convs = session_manager.conversation_manager.get_user_conversations(user_id)
    return {"active_sessions": len(user_convs)}

