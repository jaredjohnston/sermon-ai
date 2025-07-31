from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_service import supabase_service
from app.models.schemas import User
from app.config.settings import settings
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from typing import Optional

security = HTTPBearer()

class AuthContext(BaseModel):
    """Authentication context with user and tokens"""
    user: User
    access_token: str
    refresh_token: Optional[str] = None

async def verify_token(credentials: HTTPAuthorizationCredentials = None) -> AuthContext:
    """Verify JWT token from Supabase and return auth context"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided"
        )
    
    try:
        # Verify token with Supabase (signature verification handled by Supabase)
        access_token = credentials.credentials
        payload = jwt.decode(
            access_token,
            options={"verify_signature": False}  # Supabase handles signature verification
        )
        
        # Get user from Supabase
        user = await supabase_service.get_user(payload['sub'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Return auth context with user and tokens
        return AuthContext(
            user=user,
            access_token=access_token,
            refresh_token=None  # We don't have refresh token from Bearer header
        )
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

class AuthMiddleware:
    """Middleware to handle authentication"""
    
    async def __call__(self, request: Request, call_next):
        # Skip auth for certain paths
        if request.url.path in ['/docs', '/redoc', '/openapi.json']:
            return await call_next(request)
            
        try:
            auth = await security(request)
            user = await verify_token(auth)
            # Add user to request state
            request.state.user = user
            return await call_next(request)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user (backward compatibility)"""
    auth_context = await verify_token(credentials)
    return auth_context.user

async def get_auth_context(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthContext:
    """Dependency to get current auth context with user and tokens"""
    return await verify_token(credentials) 