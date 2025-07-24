import logging
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import User, UserCreate, SignUpResponse
from app.middleware.auth import get_current_user
from app.services.supabase_service import supabase_service
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

class SignInRequest(BaseModel):
    email: str
    password: str

class SignInResponse(BaseModel):
    user: User
    access_token: str
    token_type: str = "bearer"

@router.post("/signup", response_model=SignUpResponse)
async def sign_up(user_data: UserCreate):
    """
    Simplified Supabase signup - user provisioning now handled automatically 
    by database trigger when email is confirmed.
    """
    try:
        # Create auth user with metadata (trigger handles the rest)
        user = await supabase_service.sign_up(user_data)
        
        # Return simplified response - no profile/client data since user must confirm email first
        return SignUpResponse(
            user=user,
            profile=None,  # Will be created by trigger after email confirmation
            client=None,   # Will be created by trigger after email confirmation
            role=None,     # Will be set by trigger after email confirmation
            access_token=None  # User gets token after email confirmation
        )
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        
        # Check for specific error types to provide better user experience
        if "User already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists. Please sign in instead."
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to sign up: {str(e)}"
        )

@router.post("/signin", response_model=SignInResponse)
async def sign_in(credentials: SignInRequest):
    """Sign in a user"""
    try:
        result = await supabase_service.sign_in(
            email=credentials.email,
            password=credentials.password
        )
        
        return SignInResponse(
            user=result["user"],
            access_token=result["session"].access_token
        )
    except Exception as e:
        logger.error(f"Error signing in user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to sign in: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/signout")
async def sign_out():
    """Sign out a user (client-side token removal)"""
    return {"message": "Signed out successfully"} 