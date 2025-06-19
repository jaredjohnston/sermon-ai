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
    """Standard Supabase registration: signup → signin → profile → organization"""
    try:
        # 1. Create auth user (standard Supabase)
        user = await supabase_service.sign_up(user_data)
        
        # 2. Sign in to get session
        signin_result = await supabase_service.sign_in(user_data.email, user_data.password)
        session = signin_result["session"]
        
        # 3. Complete profile using session
        from app.models.schemas import UserProfileCreate
        profile_data = UserProfileCreate(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            country=user_data.country
        )
        profile = await supabase_service.complete_profile(profile_data, session)
        
        # 4. Create organization using session
        client = await supabase_service.create_organization(user_data.organization_name, session)
        
        return SignUpResponse(
            user=user,
            profile=profile,
            client=client,
            role="owner",
            access_token=session.access_token
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