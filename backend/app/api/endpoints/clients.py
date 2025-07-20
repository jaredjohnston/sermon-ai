import logging
from fastapi import APIRouter, HTTPException, status, Depends
from app.models.schemas import User
from app.middleware.auth import get_current_user, get_auth_context, AuthContext
from app.services.supabase_service import supabase_service
from uuid import UUID

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me")
async def get_current_client(current_user: User = Depends(get_current_user)):
    """Get the current user's client information"""
    try:
        client = await supabase_service.get_user_client(current_user.id)
        return client
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client: {str(e)}"
        )

@router.post("/")
async def create_client(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """Create a new client"""
    try:
        client = await supabase_service.create_client(name, current_user.id)
        return client
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {str(e)}"
        )

@router.get("/users")
async def list_client_users(auth: AuthContext = Depends(get_auth_context)):
    """List all users in the current user's client"""
    try:
        users = await supabase_service.get_client_users(auth.user.id, auth.access_token)
        return users
    except Exception as e:
        logger.error(f"Error listing client users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list client users: {str(e)}"
        )

@router.post("/users")
async def add_client_user(
    email: str,
    role: str = "member",
    current_user: User = Depends(get_current_user)
):
    """Add a user to the current client"""
    try:
        user = await supabase_service.add_client_user(
            email=email,
            role=role,
            added_by=current_user.id
        )
        return user
    except Exception as e:
        logger.error(f"Error adding client user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add client user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def remove_client_user(
    user_id: UUID,
    auth: AuthContext = Depends(get_auth_context)
):
    """Remove a user from the current client"""
    try:
        await supabase_service.remove_client_user(
            user_id=user_id,
            removed_by=auth.user.id,
            access_token=auth.access_token
        )
        return {"status": "success", "message": "User removed from client"}
    except Exception as e:
        logger.error(f"Error removing client user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove client user: {str(e)}"
        ) 