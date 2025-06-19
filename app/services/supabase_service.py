from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import create_client, Client
from supabase._async.client import create_client as acreate_client, AsyncClient
from app.config.settings import settings
from app.models.schemas import (
    User, UserCreate,
    UserProfile, UserProfileCreate,
    Team, TeamCreate,
    TeamMember, TeamMemberCreate,
    Video, VideoCreate,
    Transcript, TranscriptCreate,
    Client, ClientCreate,
    ClientUser, ClientUserCreate
)
import uuid

class SupabaseService:
    """Service for handling Supabase operations"""
    
    def __init__(self):
        self._anon_client: Optional[AsyncClient] = None
        self._service_client: Optional[AsyncClient] = None
    
    async def _get_anon_client(self) -> AsyncClient:
        """Get or create async Supabase client with anon key (for auth operations)"""
        if not self._anon_client:
            self._anon_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        return self._anon_client
    
    async def _get_service_client(self) -> AsyncClient:
        """Get or create async Supabase client with service role (for admin operations)"""
        if not self._service_client:
            self._service_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
        return self._service_client
    
    # Auth methods
    async def sign_up(self, user: UserCreate) -> User:
        """Register a new user"""
        try:
            client = await self._get_anon_client()
            response = await client.auth.sign_up({
                "email": user.email,
                "password": user.password
            })
            return User(**response.user.dict())
        except Exception as e:
            raise Exception(f"Failed to sign up user: {str(e)}")
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in a user"""
        try:
            client = await self._get_anon_client()
            response = await client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "user": User(**response.user.dict()),
                "session": response.session
            }
        except Exception as e:
            raise Exception(f"Failed to sign in: {str(e)}")
    
    async def complete_profile(self, profile_data: UserProfileCreate, session) -> UserProfile:
        """Complete user profile using authenticated session - standard Supabase pattern"""
        try:
            # Create client with user's session (standard pattern)
            client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            await client.auth.set_session(session.access_token, session.refresh_token)
            
            # Insert profile - audit fields handled by trigger using auth.uid()
            response = await client.table('user_profiles').insert({
                "user_id": session.user.id,
                "first_name": profile_data.first_name,
                "last_name": profile_data.last_name,
                "country": profile_data.country,
                "phone": profile_data.phone,
                "bio": profile_data.bio,
                "avatar_url": profile_data.avatar_url,
            }).execute()
            
            return UserProfile(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to complete profile: {str(e)}")
    
    async def create_organization(self, org_name: str, session) -> Client:
        """Create organization using authenticated session - standard Supabase pattern"""
        try:
            # Create client with user's session (standard pattern)
            client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            await client.auth.set_session(session.access_token, session.refresh_token)
            
            # Create organization/client - audit fields handled by trigger using auth.uid()
            response = await client.table('clients').insert({
                "name": org_name,
            }).execute()
            
            org = Client(**response.data[0])
            
            # Link user to organization as owner
            await client.table('client_users').insert({
                "client_id": str(org.id),
                "user_id": session.user.id,
                "role": "owner"
            }).execute()
            
            return org
        except Exception as e:
            raise Exception(f"Failed to create organization: {str(e)}")
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user details"""
        try:
            client = await self._get_service_client()
            response = await client.auth.admin.get_user_by_id(str(user_id))
            return User(**response.user.dict()) if response.user else None
        except Exception as e:
            raise Exception(f"Failed to get user: {str(e)}")
    
    # User Profile methods
    async def create_user_profile_with_session(self, profile: UserProfileCreate, user_id: UUID, access_token: str, refresh_token: str) -> UserProfile:
        """Create a user profile using the user's session (for RLS compliance)"""
        try:
            # Create client with user's session token for RLS compliance
            user_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            
            # Set the user's session with both tokens
            await user_client.auth.set_session(access_token, refresh_token)
            
            # Debug: Check if session is properly set
            current_user = await user_client.auth.get_user()
            user_id_from_session = current_user.user.id if current_user and current_user.user else None
            print(f"DEBUG: User after setting session: {user_id_from_session}")
            print(f"DEBUG: Expected user_id: {user_id}")
            
            if not user_id_from_session:
                print("DEBUG: Session not set properly, auth.uid() will be None")
            
            response = await user_client.table('user_profiles').insert({
                "user_id": str(user_id),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "country": profile.country,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": profile.avatar_url,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            
            if not response.data:
                raise Exception("Failed to create user profile - no data returned")
            
            return UserProfile(**response.data[0])
            
        except Exception as e:
            raise Exception(f"Failed to create user profile: {str(e)}")

    async def create_user_profile(self, profile: UserProfileCreate, user_id: UUID) -> UserProfile:
        """Create a user profile using service role (admin bypass)"""
        try:
            client = await self._get_service_client()
            
            # First attempt: let trigger handle audit fields
            try:
                response = await client.table('user_profiles').insert({
                    "user_id": str(user_id),
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "country": profile.country,
                    "phone": profile.phone,
                    "bio": profile.bio,
                    "avatar_url": profile.avatar_url,
                }).execute()
            except Exception:
                # Fallback: insert with explicit audit fields for service role
                response = await client.table('user_profiles').insert({
                    "user_id": str(user_id),
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                    "country": profile.country,
                    "phone": profile.phone,
                    "bio": profile.bio,
                    "avatar_url": profile.avatar_url,
                    "created_by": str(user_id),
                    "updated_by": str(user_id)
                }).execute()
            return UserProfile(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to create user profile: {str(e)}")
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """Get user profile by user_id"""
        try:
            client = await self._get_client()
            response = await client.table('user_profiles')\
                .select("*")\
                .eq("user_id", str(user_id))\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            return UserProfile(**response.data) if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get user profile: {str(e)}")
    
    async def update_user_profile(self, user_id: UUID, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile"""
        try:
            client = await self._get_client()
            # Always update the updated_by field
            updates["updated_by"] = str(user_id)
            
            response = await client.table('user_profiles')\
                .update(updates)\
                .eq("user_id", str(user_id))\
                .execute()
            return UserProfile(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to update user profile: {str(e)}")
    
    # Team methods
    async def create_team(self, team: TeamCreate, user_id: UUID) -> Team:
        """Create a new team"""
        try:
            client = await self._get_client()
            response = await client.table('teams').insert({
                "name": team.name,
            }).execute()
            
            team_data = response.data[0]
            
            # Add creator as admin
            await client.table('team_members').insert({
                "team_id": team_data["id"],
                "user_id": str(user_id),
                "role": "admin"
            }).execute()
            
            return Team(**team_data)
        except Exception as e:
            raise Exception(f"Failed to create team: {str(e)}")
    
    async def get_user_teams(self, user_id: UUID) -> List[Team]:
        """Get teams for a user"""
        try:
            client = await self._get_client()
            response = await client.table('teams')\
                .select("*")\
                .eq("id", client.table('team_members')\
                    .select("team_id")\
                    .eq("user_id", str(user_id)))\
                .execute()
            return [Team(**team) for team in response.data]
        except Exception as e:
            raise Exception(f"Failed to get user teams: {str(e)}")
    
    # Video methods
    async def create_video(self, video: VideoCreate, user_id: UUID) -> Video:
        """Create a new video record"""
        try:
            client = await self._get_service_client()
            response = await client.table('videos').insert({
                "filename": video.filename,
                "storage_path": video.storage_path,
                "content_type": video.content_type,
                "size_bytes": video.size_bytes,
                "client_id": str(video.client_id) if video.client_id else None,
                "user_id": str(user_id),
                "metadata": video.metadata,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            return Video(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to create video: {str(e)}")
    
    async def get_user_videos(self, user_id: UUID) -> List[Video]:
        """Get videos for a user"""
        try:
            client = await self._get_client()
            response = await client.table('videos')\
                .select("*")\
                .eq("user_id", str(user_id))\
                .execute()
            return [Video(**video) for video in response.data]
        except Exception as e:
            raise Exception(f"Failed to get user videos: {str(e)}")
    
    # Transcript methods
    async def create_transcript(self, transcript: TranscriptCreate, user_id: UUID) -> Transcript:
        """Create a new transcript"""
        try:
            client = await self._get_service_client()
            response = await client.table('transcripts').insert({
                "video_id": str(transcript.video_id),
                "client_id": str(transcript.client_id),
                "user_id": str(user_id),
                "status": transcript.status,
                "raw_transcript": transcript.raw_transcript,
                "processed_transcript": transcript.processed_transcript,
                "error_message": transcript.error_message,
                "request_id": transcript.request_id,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to create transcript: {str(e)}")
    
    async def update_transcript(self, transcript_id: UUID, updates: Dict[str, Any], user_id: UUID) -> Transcript:
        """Update a transcript"""
        try:
            client = await self._get_client()
            # Always update the updated_by field
            updates["updated_by"] = str(user_id)
            
            # If setting deleted_at, also set deleted_by
            if updates.get("deleted_at"):
                updates["deleted_by"] = str(user_id)
            
            response = await client.table('transcripts')\
                .update(updates)\
                .eq("id", str(transcript_id))\
                .execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to update transcript: {str(e)}")

    async def get_transcript_by_request_id(self, request_id: str) -> Optional[Transcript]:
        """Get a transcript by its Deepgram request ID"""
        try:
            client = await self._get_client()
            response = await client.table('transcripts')\
                .select("*")\
                .eq("request_id", request_id)\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            return Transcript(**response.data) if response.data else None
        except Exception as e:
            raise Exception(f"Failed to get transcript by request_id: {str(e)}")

    async def get_client_transcripts(self, client_id: UUID) -> List[Transcript]:
        """Get all transcripts for a client"""
        try:
            client = await self._get_client()
            response = await client.table('transcripts')\
                .select("*")\
                .eq("client_id", str(client_id))\
                .is_("deleted_at", "null")\
                .execute()
            return [Transcript(**transcript) for transcript in response.data]
        except Exception as e:
            raise Exception(f"Failed to get client transcripts: {str(e)}")

    # Client methods
    async def create_client_with_session(self, name: str, user_id: UUID, access_token: str, refresh_token: str) -> Client:
        """Create a new client using user's session (for RLS compliance) and add the creator as owner"""
        try:
            # Create client with user's session token for RLS compliance
            user_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            
            # Set the user's session with both tokens
            await user_client.auth.set_session(access_token, refresh_token)
            
            # Debug: Check if session is properly set for client creation
            current_user = await user_client.auth.get_user()
            user_id_from_session = current_user.user.id if current_user and current_user.user else None
            print(f"DEBUG CLIENT: User after setting session: {user_id_from_session}")
            print(f"DEBUG CLIENT: Expected user_id: {user_id}")
            
            if not user_id_from_session:
                print("DEBUG CLIENT: Session not set properly, auth.uid() will be None")
            
            # Create client
            client_response = await user_client.table('clients').insert({
                "name": name,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            
            client_data = client_response.data[0]
            
            # Add creator as owner using service role (admin operation)
            service_client = await self._get_service_client()
            await service_client.table('client_users').insert({
                "client_id": client_data["id"],
                "user_id": str(user_id),
                "role": "owner",
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            
            return Client(**client_data)
            
        except Exception as e:
            raise Exception(f"Failed to create client: {str(e)}")

    async def create_client(self, name: str, user_id: UUID) -> Client:
        """Create a new client and add the creator as owner"""
        try:
            client = await self._get_service_client()
            # Create client
            client_response = await client.table('clients').insert({
                "name": name,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            
            client_data = client_response.data[0]
            
            # Add creator as owner
            await client.table('client_users').insert({
                "client_id": client_data["id"],
                "user_id": str(user_id),
                "role": "owner",
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            
            return Client(**client_data)
        except Exception as e:
            raise Exception(f"Failed to create client: {str(e)}")
    
    async def get_user_client(self, user_id: UUID, client_id: Optional[UUID] = None) -> Optional[Client]:
        """Get a user's client information with optional admin bypass"""
        try:
            client = await self._get_service_client()
            
            # Admin bypass for testing - allow switching between clients
            if client_id and await self._is_admin_user(user_id):
                client_response = await client.table('clients')\
                    .select("*")\
                    .eq("id", str(client_id))\
                    .is_("deleted_at", "null")\
                    .single()\
                    .execute()
                return Client(**client_response.data) if client_response.data else None
            
            # Regular flow - get user's assigned client
            client_user_response = await client.table('client_users')\
                .select("client_id")\
                .eq("user_id", str(user_id))\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            
            if not client_user_response.data:
                return None
            
            # Get client details
            client_response = await client.table('clients')\
                .select("*")\
                .eq("id", client_user_response.data["client_id"])\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            
            return Client(**client_response.data) if client_response.data else None
        except Exception as e:
            raise Exception(f"Failed to get user client: {str(e)}")
    
    async def _is_admin_user(self, user_id: UUID) -> bool:
        """Check if user is admin for testing purposes"""
        from app.config.settings import settings
        
        # Only allow admin bypass in development/staging
        if settings.ENVIRONMENT == "production":
            return False
        
        try:
            # Get user's email from auth system
            client = await self._get_client()
            user_response = await client.auth.admin.get_user_by_id(str(user_id))
            
            if user_response.user and user_response.user.email:
                # Check if user's email matches admin email
                return user_response.user.email.lower() == settings.ADMIN_EMAIL.lower()
                
        except Exception as e:
            # If we can't check, assume not admin for security
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to check admin status for user {user_id}: {str(e)}")
            
        return False
    
    async def get_client_users(self, user_id: UUID) -> List[ClientUser]:
        """Get all users in a client"""
        try:
            client = await self._get_client()
            # First get user's client_id
            user_client = await self.get_user_client(user_id)
            if not user_client:
                return []
            
            # Get all users in the client
            response = await client.table('client_users')\
                .select("*")\
                .eq("client_id", str(user_client.id))\
                .is_("deleted_at", "null")\
                .execute()
            
            return [ClientUser(**user) for user in response.data]
        except Exception as e:
            raise Exception(f"Failed to get client users: {str(e)}")
    
    async def add_client_user(self, email: str, role: str, added_by: UUID) -> ClientUser:
        """Add a user to a client"""
        try:
            client = await self._get_client()
            # Get the client of the user adding
            user_client = await self.get_user_client(added_by)
            if not user_client:
                raise Exception("User is not associated with any client")
            
            # Check if user exists, if not create them
            user_response = await client.auth.admin.list_users()
            user = next((u for u in user_response.users if u.email == email), None)
            
            if not user:
                # Create user with temporary password
                user = await self.sign_up(UserCreate(
                    email=email,
                    password=uuid.uuid4().hex  # Random temporary password
                ))
            
            # Check if user already belongs to a client
            existing_client = await self.get_user_client(UUID(user.id))
            if existing_client:
                raise Exception(f"User already belongs to client: {existing_client.name}")
            
            # Add user to client
            response = await client.table('client_users').insert({
                "client_id": str(user_client.id),
                "user_id": str(user.id),
                "role": role,
                "created_by": str(added_by),
                "updated_by": str(added_by)
            }).execute()
            
            return ClientUser(**response.data[0])
        except Exception as e:
            raise Exception(f"Failed to add client user: {str(e)}")
    
    async def remove_client_user(self, user_id: UUID, removed_by: UUID) -> None:
        """Remove a user from a client (soft delete)"""
        try:
            client = await self._get_client()
            # Get the client of the user removing
            user_client = await self.get_user_client(removed_by)
            if not user_client:
                raise Exception("User is not associated with any client")
            
            # Soft delete the user from the client
            await client.table('client_users')\
                .update({
                    "deleted_at": "now()",
                    "deleted_by": str(removed_by),
                    "updated_by": str(removed_by)
                })\
                .eq("client_id", str(user_client.id))\
                .eq("user_id", str(user_id))\
                .is_("deleted_at", "null")\
                .execute()
        except Exception as e:
            raise Exception(f"Failed to remove client user: {str(e)}")

    async def get_client_videos(self, client_id: UUID) -> List[Video]:
        """Get videos for a client"""
        try:
            client = await self._get_client()
            response = await client.table('videos')\
                .select("*")\
                .eq("client_id", str(client_id))\
                .is_("deleted_at", "null")\
                .execute()
            return [Video(**video) for video in response.data]
        except Exception as e:
            raise Exception(f"Failed to get client videos: {str(e)}")

# Create a singleton instance
supabase_service = SupabaseService() 