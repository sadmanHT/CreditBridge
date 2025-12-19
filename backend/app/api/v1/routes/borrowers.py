"""
Borrower Profile Routes for CreditBridge

These endpoints manage borrower profiles and are protected by authentication.
Each borrower profile is linked to a Supabase Auth user.

Design constraints:
- JWT-based authentication (Supabase access token)
- Free tier only
- Privacy-first (no sensitive raw data)
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from app.core.supabase import supabase
from app.core.repository import create_borrower

router = APIRouter(prefix="/borrowers")


class BorrowerProfileCreate(BaseModel):
    full_name: str
    gender: str
    region: str


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Dependency to extract and verify the authenticated user from the JWT token.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        User ID of the authenticated user
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use 'Bearer <token>'"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        response = supabase.auth.get_user(token)
        
        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        return response.user.id
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/me")
async def create_my_profile(
    profile: BorrowerProfileCreate,
    user_id: str = Depends(get_current_user)
):
    """
    Create a borrower profile for the authenticated user.
    
    Args:
        profile: Borrower profile data (full_name, gender, region)
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Created borrower profile
        
    Raises:
        HTTPException: If profile creation fails
    """
    try:
        borrower = create_borrower(
            user_id=user_id,
            full_name=profile.full_name,
            gender=profile.gender,
            region=profile.region
        )
        return borrower
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create borrower profile: {str(e)}"
        )


@router.get("/me")
async def get_my_profile(user_id: str = Depends(get_current_user)):
    """
    Fetch the borrower profile for the authenticated user.
    
    Args:
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Borrower profile data
        
    Raises:
        HTTPException: If profile not found or fetch fails
    """
    try:
        response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found. Please create your profile first."
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch borrower profile: {str(e)}"
        )
