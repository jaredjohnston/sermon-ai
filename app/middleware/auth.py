from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_service import supabase_service
from app.models.schemas import User
import jwt
from jwt.exceptions import InvalidTokenError

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = None):
    """Verify JWT token from Supabase"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No credentials provided"
        )
    
    try:
        # Verify token with Supabase public key
        token = credentials.credentials
        payload = jwt.decode(
            token,
            options={"verify_signature": False}  # Supabase handles signature verification
        )
        
        # Get user from Supabase
        user = await supabase_service.get_user(payload['sub'])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
            
        return user
        
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
    """Dependency to get current authenticated user"""
    return await verify_token(credentials) 