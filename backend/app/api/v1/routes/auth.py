"""
Authentication Routes for CreditBridge (Borrower-focused)

These endpoints handle:
- Borrower signup (email + password)
- Borrower login
- Token-based identity verification

Constraints:
- Use Supabase Auth (free tier only)
- No paid OAuth providers
- Simple, explicit error messages
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.core.supabase import supabase, supabase_admin

router = APIRouter(prefix="/auth")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(request: SignupRequest):
    """
    Register a new borrower account using Supabase Auth.
    
    Args:
        request: Signup credentials (email and password)
        
    Returns:
        User information including ID and email
        
    Raises:
        HTTPException: If signup fails
    """
    try:
        # Create user via Supabase Auth
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=400,
                detail="Signup failed. Please check your credentials."
            )
        
        # If email confirmation is required and session is None,
        # use admin client to auto-confirm for development
        access_token = None
        if response.session:
            access_token = response.session.access_token
        elif supabase_admin:
            # Auto-confirm email using admin client for development
            try:
                # Update user to confirm email - correct parameter is email_confirmed
                supabase_admin.auth.admin.update_user_by_id(
                    response.user.id,
                    {"email_confirmed_at": "now()"}  # Mark email as confirmed
                )
                
                # Give a moment for the update to propagate
                import time
                time.sleep(0.5)
                
                # Now sign in to get session
                login_response = supabase.auth.sign_in_with_password({
                    "email": request.email,
                    "password": request.password
                })
                
                if login_response.session:
                    access_token = login_response.session.access_token
            except Exception as e:
                # If auto-confirm fails, log the error
                import logging
                logging.error(f"Auto-confirm failed: {e}")
                print(f"⚠️  Auto-confirm failed: {e}")
        
        # Return user info and access token
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "access_token": access_token,
            "message": "User created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login")
async def login(request: LoginRequest):
    """
    Authenticate a borrower and return access token.
    
    Args:
        request: Login credentials (email and password)
        
    Returns:
        Access token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate via Supabase
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user": {
                "user_id": response.user.id,
                "email": response.user.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Login failed: {str(e)}"
        )
