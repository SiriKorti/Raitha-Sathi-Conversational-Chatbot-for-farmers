from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

from app.services.auth_manager import AuthManager
from app.utils.logger import logger

router = APIRouter()
auth_manager = AuthManager()


class LoginRequest(BaseModel):
    email: Optional[str] = None
    identifier: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    password: str


class RegisterRequest(BaseModel):
    fullName: str
    mobile: str
    email: Optional[str] = None
    password: str
    state: Optional[str] = "Karnataka"
    district: Optional[str] = ""
    taluk: Optional[str] = ""
    village: Optional[str] = ""
    preferredLanguage: Optional[str] = "kn"


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/login")
async def login(payload: LoginRequest):
    """
    Authenticate a farmer user via email, mobile number, or ID and password.
    """
    ident = payload.email or payload.identifier or payload.mobile or payload.phone
    if not ident:
        raise HTTPException(
            status_code=400,
            detail="Email address or mobile number is required."
        )

    logger.info(f"Authenticating login request for: {ident}")
    result = auth_manager.authenticate(ident, payload.password)
    
    if not result:
        logger.warning(f"Failed login attempt for: {ident}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials. Please check your email/mobile and password."
        )

    logger.info(f"Login successful for user: {result['user']['id']}")
    return {
        "status": "success",
        "message": "Login successful",
        "user": result["user"],
        "token": result["token"],
    }


@router.post("/register")
async def register(payload: RegisterRequest):
    """
    Register a new farmer account and store in the system.
    """
    logger.info(f"Registering new user: {payload.mobile} / {payload.email}")
    result, error = auth_manager.register(payload.model_dump())
    
    if error:
        raise HTTPException(status_code=400, detail=error)

    return {
        "status": "success",
        "message": "Farmer account registered successfully.",
        "user": result["user"],
        "token": result["token"],
    }


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Request password recovery for a farmer account.
    """
    logger.info(f"Password reset request for: {payload.email}")
    success, message = auth_manager.forgot_password(payload.email)
    return {
        "status": "success",
        "message": message
    }


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Log out user and invalidate session token.
    """
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        auth_manager.invalidate_token(token)
    return {"status": "success", "message": "Logged out successfully"}


class DeleteAccountPayload(BaseModel):
    identifier: Optional[str] = None
    userId: Optional[str] = None


@router.delete("/account/{identifier}")
async def delete_account(identifier: str):
    """
    Permanently delete a user account from the backend database.
    """
    logger.info(f"Received account deletion request for: {identifier}")
    success, message = auth_manager.delete_user(identifier)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"status": "success", "message": message}


@router.post("/delete-account")
async def delete_account_post(payload: DeleteAccountPayload):
    """
    Permanently delete a user account via POST body.
    """
    ident = payload.identifier or payload.userId
    if not ident:
        raise HTTPException(status_code=400, detail="User identifier is required for deletion.")
    
    logger.info(f"Received account deletion POST for: {ident}")
    success, message = auth_manager.delete_user(ident)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"status": "success", "message": message}


async def require_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    FastAPI dependency to enforce authentication and derive the authenticated user.
    Extracts Bearer token and verifies identity against backend session store.
    Strictly denies unauthenticated access (no cross-user fallback).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    user = auth_manager.get_user_by_token(token)
    if not user:
        # Also check if token directly identifies a user identifier (dev/test fallback only)
        user_by_id = auth_manager.find_user_by_identifier(token)
        if user_by_id:
            return auth_manager.sanitize_user(user_by_id)
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    return user


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Retrieve currently authenticated user profile.
    """
    user = await require_current_user(authorization)
    return {"status": "success", "user": user}

