from typing import Optional, List, Dict, Any
from uuid import UUID
from pathlib import Path
from supabase import create_client, Client
from supabase._async.client import create_client as acreate_client, AsyncClient
from app.config.settings import settings
from app.models.schemas import (
    User, UserCreate,
    UserProfile, UserProfileCreate,
    Team, TeamCreate,
    TeamMember, TeamMemberCreate,
    Media, MediaCreate, Video, VideoCreate,  # Media models + backward compatibility
    Transcript, TranscriptCreate,
    Client, ClientCreate,
    ClientUser, ClientUserCreate
)
import uuid
import logging
from datetime import datetime, UTC
from fastapi import UploadFile


# Custom exceptions for better error handling
class SupabaseServiceError(Exception):
    """Base exception for SupabaseService errors"""
    pass

class AuthenticationError(SupabaseServiceError):
    """Raised when authentication fails"""
    pass

class DatabaseError(SupabaseServiceError):
    """Raised when database operations fail"""
    pass

class NotFoundError(SupabaseServiceError):
    """Raised when requested resource is not found"""
    pass

class ValidationError(SupabaseServiceError):
    """Raised when data validation fails"""
    pass

class SupabaseService:
    """Service for handling Supabase operations"""
    
    def __init__(self):
        self._anon_client: Optional[AsyncClient] = None
        self._service_client: Optional[AsyncClient] = None
        self._current_loop = None
        self.logger = logging.getLogger(__name__)
    
    def _check_event_loop(self):
        """Check if we're in a different event loop and reset clients if needed"""
        try:
            import asyncio
            current_loop = asyncio.get_running_loop()
            if self._current_loop != current_loop:
                # Event loop has changed, reset clients
                if self._anon_client:
                    self._anon_client = None
                if self._service_client:
                    self._service_client = None
                self._current_loop = current_loop
        except RuntimeError:
            # No running event loop
            pass
    
    async def _get_anon_client(self) -> AsyncClient:
        """Get or create async Supabase client with anon key (for auth operations)"""
        self._check_event_loop()
        if not self._anon_client:
            self._anon_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
        return self._anon_client
    
    async def _get_service_client(self) -> AsyncClient:
        """Get or create async Supabase client with service role (for admin operations)"""
        self._check_event_loop()
        if not self._service_client:
            self._service_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
        return self._service_client
    
    async def _get_client(self) -> AsyncClient:
        """Get default async Supabase client (service role for most operations)"""
        return await self._get_service_client()
    
    async def create_user_authenticated_client(self, access_token: str, refresh_token: str = None) -> AsyncClient:
        """Create user-authenticated client for operations requiring user context"""
        client = await acreate_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        if refresh_token:
            await client.auth.set_session(access_token, refresh_token)
        else:
            # Set just the access token for operations
            client.options.headers["Authorization"] = f"Bearer {access_token}"
        return client
    
    def _uuid_str(self, uuid_value: UUID) -> str:
        """Helper method to convert UUID to string consistently"""
        return str(uuid_value)
    
    def _validate_uuid(self, uuid_value: UUID, field_name: str = "UUID") -> UUID:
        """Validate UUID input and raise appropriate error if invalid"""
        if not uuid_value:
            raise ValidationError(f"{field_name} cannot be None")
        if not isinstance(uuid_value, UUID):
            raise ValidationError(f"Invalid {field_name}: must be a valid UUID")
        return uuid_value
    
    def _validate_email(self, email: str) -> str:
        """Basic email validation"""
        if not email or not email.strip():
            raise ValidationError("Email cannot be empty")
        if "@" not in email or "." not in email:
            raise ValidationError("Invalid email format")
        return email.strip().lower()
    
    def _validate_string(self, value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
        """Validate string input with length constraints"""
        if not value or not value.strip():
            raise ValidationError(f"{field_name} cannot be empty")
        if len(value.strip()) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")
        if len(value.strip()) > max_length:
            raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
        return value.strip()
    
    # Auth methods
    async def sign_up(self, user: UserCreate) -> User:
        """Register a new user"""
        try:
            # Validate input
            email = self._validate_email(user.email)
            if not user.password or len(user.password) < 8:
                raise ValidationError("Password must be at least 8 characters")
            
            client = await self._get_anon_client()
            response = await client.auth.sign_up({
                "email": email,
                "password": user.password
            })
            return User(**response.user.dict())
        except (ValidationError, AuthenticationError):
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to sign up user: {str(e)}") from e
    
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
            raise AuthenticationError(f"Failed to sign in: {str(e)}") from e
    
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
            raise DatabaseError(f"Failed to complete profile: {str(e)}") from e
    
    async def create_organization(self, org_name: str, session) -> Client:
        """Create organization using service role - system operation during signup"""
        try:
            # Use service role for organization creation (system operation)
            client = await self._get_service_client()
            
            # Create organization/client - audit fields handled by trigger with system user
            response = await client.table('clients').insert({
                "name": org_name,
            }).execute()
            
            org = Client(**response.data[0])
            
            # Link user to organization as owner using service role
            await client.table('client_users').insert({
                "client_id": str(org.id),
                "user_id": session.user.id,
                "role": "owner"
            }).execute()
            
            return org
        except Exception as e:
            raise DatabaseError(f"Failed to create organization: {str(e)}") from e
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user details"""
        try:
            client = await self._get_service_client()
            response = await client.auth.admin.get_user_by_id(str(user_id))
            return User(**response.user.dict()) if response.user else None
        except Exception as e:
            raise DatabaseError(f"Failed to get user: {str(e)}") from e
    
    # User Profile methods
    async def create_user_profile(self, profile: UserProfileCreate, user_id: UUID) -> UserProfile:
        """Create a user profile using service role with proper audit fields"""
        try:
            client = await self._get_service_client()
            response = await client.table('user_profiles').insert({
                "user_id": self._uuid_str(user_id),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "country": profile.country,
                "phone": profile.phone,
                "bio": profile.bio,
                "avatar_url": profile.avatar_url,
                "created_by": self._uuid_str(user_id),
                "updated_by": self._uuid_str(user_id)
            }).execute()
            
            if not response.data:
                raise DatabaseError("Failed to create user profile - no data returned")
                
            return UserProfile(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create user profile: {str(e)}") from e
    
    async def get_user_profile(self, user_id: UUID, access_token: str, refresh_token: str = None) -> Optional[UserProfile]:
        """Get user profile by user_id using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('user_profiles')\
                .select("*")\
                .eq("user_id", str(user_id))\
                .is_("deleted_at", "null")\
                .single()\
                .execute()
            return UserProfile(**response.data) if response.data else None
        except Exception as e:
            raise DatabaseError(f"Failed to get user profile: {str(e)}") from e
    
    async def update_user_profile(self, user_id: UUID, updates: Dict[str, Any], access_token: str, refresh_token: str = None) -> UserProfile:
        """Update user profile using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            # Remove manual audit field - handled by triggers with user context
            
            response = await client.table('user_profiles')\
                .update(updates)\
                .eq("user_id", str(user_id))\
                .execute()
            return UserProfile(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to update user profile: {str(e)}") from e
    
    # Team methods
    async def create_team(self, team: TeamCreate, user_id: UUID, access_token: str, refresh_token: str = None) -> Team:
        """Create a new team using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
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
            raise DatabaseError(f"Failed to create team: {str(e)}") from e
    
    async def get_user_teams(self, user_id: UUID, access_token: str, refresh_token: str = None) -> List[Team]:
        """Get teams for a user using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('teams')\
                .select("*")\
                .eq("id", client.table('team_members')\
                    .select("team_id")\
                    .eq("user_id", str(user_id)))\
                .execute()
            return [Team(**team) for team in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get user teams: {str(e)}") from e
    
    # Media methods (videos, audio, documents)
    async def create_media(self, media: MediaCreate, user_id: UUID) -> Media:
        """Create a new media record (video, audio, or document)"""
        try:
            client = await self._get_service_client()
            response = await client.table('media').insert({
                "filename": media.filename,
                "storage_path": media.storage_path,
                "content_type": media.content_type,
                "size_bytes": media.size_bytes,
                "client_id": str(media.client_id) if media.client_id else None,
                "user_id": str(user_id),
                "metadata": media.metadata,
                "created_by": str(user_id),
                "updated_by": str(user_id)
            }).execute()
            return Media(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create media: {str(e)}") from e
    
    async def delete_media(self, media_id: UUID, user_id: UUID) -> bool:
        """Delete a media record (soft delete)"""
        try:
            client = await self._get_service_client()
            response = await client.table('media').update({
                "deleted_at": datetime.now(UTC).isoformat(),
                "deleted_by": str(user_id),
                "updated_by": str(user_id)
            }).eq('id', str(media_id)).execute()
            
            return len(response.data) > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete media: {str(e)}") from e

    async def update_media(self, media_id: UUID, updates: Dict[str, Any], user_id: UUID) -> Media:
        """Update a media record"""
        try:
            client = await self._get_service_client()
            
            # Add updated_by to the updates
            updates_with_meta = {
                **updates,
                "updated_by": str(user_id)
            }
            
            response = await client.table('media').update(updates_with_meta).eq('id', str(media_id)).execute()
            
            if not response.data:
                raise NotFoundError(f"Media not found: {media_id}")
            
            return Media(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to update media: {str(e)}") from e

    async def get_media(self, media_id: UUID, access_token: str) -> Media:
        """Get a single media record by ID"""
        try:
            if access_token == settings.SUPABASE_SERVICE_ROLE_KEY:
                # Use service client for system operations
                client = await self._get_service_client()
            else:
                # Use user-authenticated client
                client = await self.create_user_authenticated_client(access_token)
            
            response = await client.table('media').select("*").eq('id', str(media_id)).is_('deleted_at', 'null').execute()
            
            if not response.data:
                raise NotFoundError(f"Media not found: {media_id}")
            
            return Media(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to get media: {str(e)}") from e

    async def get_media_by_filename_and_client(self, filename: str, client_id: str, access_token: str) -> List[Media]:
        """Get media records by filename and client_id"""
        try:
            if access_token == settings.SUPABASE_SERVICE_ROLE_KEY:
                # Use service client for system operations
                client = await self._get_service_client()
            else:
                # Use user-authenticated client
                client = await self.create_user_authenticated_client(access_token)
            
            response = await client.table('media').select("*").eq('filename', filename).eq('client_id', client_id).is_('deleted_at', 'null').order('created_at', desc=True).execute()
            
            return [Media(**item) for item in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get media by filename and client: {str(e)}") from e

    async def get_media_by_storage_path(self, storage_path: str, access_token: str) -> List[Media]:
        """Get media records by storage_path (more reliable than filename matching)"""
        try:
            if access_token == settings.SUPABASE_SERVICE_ROLE_KEY:
                # Use service client for system operations
                client = await self._get_service_client()
            else:
                # Use user-authenticated client
                client = await self.create_user_authenticated_client(access_token)
            
            response = await client.table('media').select("*").eq('storage_path', storage_path).is_('deleted_at', 'null').order('created_at', desc=True).execute()
            
            return [Media(**item) for item in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get media by storage path: {str(e)}") from e
    
    # Backward compatibility method
    async def create_video(self, video: VideoCreate, user_id: UUID) -> Video:
        """Create a new video record (backward compatibility)"""
        return await self.create_media(video, user_id)
    
    async def get_user_media(self, user_id: UUID, access_token: str, refresh_token: str = None) -> List[Media]:
        """Get all media for a user using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('media')\
                .select("*")\
                .eq("user_id", str(user_id))\
                .execute()
            return [Media(**media) for media in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get user media: {str(e)}") from e
    
    # Backward compatibility method
    async def get_user_videos(self, user_id: UUID, access_token: str, refresh_token: str = None) -> List[Video]:
        """Get videos for a user (backward compatibility)"""
        return await self.get_user_media(user_id, access_token, refresh_token)
    
    # Transcript methods
    async def create_transcript(self, transcript: TranscriptCreate, user_id: UUID, access_token: str, refresh_token: str = None) -> Transcript:
        """Create a new transcript using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            # Audit fields handled automatically by triggers with user context
            response = await client.table('transcripts').insert({
                "media_id": str(transcript.media_id),
                "client_id": str(transcript.client_id),
                "user_id": str(user_id),
                "status": transcript.status,
                "raw_transcript": transcript.raw_transcript,
                "processed_transcript": transcript.processed_transcript,
                "error_message": transcript.error_message,
                "request_id": transcript.request_id
            }).execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create transcript: {str(e)}") from e
    
    async def create_transcript_system(self, transcript: TranscriptCreate, user_id: UUID) -> Transcript:
        """Create a new transcript using service role with explicit audit fields"""
        try:
            client = await self._get_service_client()
            # Explicitly set audit fields since we're using service role
            response = await client.table('transcripts').insert({
                "media_id": str(transcript.media_id),
                "client_id": str(transcript.client_id),
                "user_id": str(user_id),
                "status": transcript.status,
                "raw_transcript": transcript.raw_transcript,
                "processed_transcript": transcript.processed_transcript,
                "error_message": transcript.error_message,
                "request_id": transcript.request_id,
                "metadata": transcript.metadata,
                "created_by": str(user_id),  # Explicit audit field
                "updated_by": str(user_id)   # Explicit audit field
            }).execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to create transcript (system): {str(e)}") from e
    
    async def update_transcript(self, transcript_id: UUID, updates: Dict[str, Any], user_id: UUID, access_token: str, refresh_token: str = None) -> Transcript:
        """Update a transcript using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            # Audit fields handled automatically by triggers with user context
            
            response = await client.table('transcripts')\
                .update(updates)\
                .eq("id", str(transcript_id))\
                .execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to update transcript: {str(e)}") from e
    
    async def update_transcript_system(self, transcript_id: UUID, updates: Dict[str, Any], user_id: UUID) -> Transcript:
        """Update a transcript using service role with explicit audit fields"""
        try:
            client = await self._get_service_client()
            # Add explicit audit field for updates
            updates_with_audit = {
                **updates,
                "updated_by": str(user_id)  # Explicit audit field
            }
            
            response = await client.table('transcripts')\
                .update(updates_with_audit)\
                .eq("id", str(transcript_id))\
                .execute()
            return Transcript(**response.data[0])
        except Exception as e:
            raise DatabaseError(f"Failed to update transcript (system): {str(e)}") from e

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
            raise DatabaseError(f"Failed to get transcript by request_id: {str(e)}") from e
    
    async def get_transcript_by_id(self, transcript_id: str) -> Optional[Transcript]:
        """Get a transcript by its ID using service role (for system operations)"""
        try:
            client = await self._get_client()
            response = await client.table('transcripts')\
                .select("*")\
                .eq("id", transcript_id)\
                .is_("deleted_at", "null")\
                .maybe_single()\
                .execute()
            return Transcript(**response.data) if response and response.data else None
        except Exception as e:
            raise DatabaseError(f"Failed to get transcript by id: {str(e)}") from e

    async def get_client_transcripts(self, client_id: UUID, access_token: str, refresh_token: str = None) -> List[Transcript]:
        """Get all transcripts for a client using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('transcripts')\
                .select("*")\
                .eq("client_id", str(client_id))\
                .is_("deleted_at", "null")\
                .execute()
            return [Transcript(**transcript) for transcript in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get client transcripts: {str(e)}") from e

    async def get_transcript(self, transcript_id: UUID, access_token: str, refresh_token: str = None) -> Optional[Transcript]:
        """Get a single transcript by ID using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('transcripts')\
                .select("*")\
                .eq("id", self._uuid_str(transcript_id))\
                .is_("deleted_at", "null")\
                .maybe_single()\
                .execute()
            return Transcript(**response.data) if response and response.data else None
        except Exception as e:
            raise DatabaseError(f"Failed to get transcript: {str(e)}") from e

    async def get_user_transcripts(self, user_id: UUID, access_token: str, refresh_token: str = None) -> List[Transcript]:
        """Get all transcripts for a user using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('transcripts')\
                .select("*")\
                .eq("created_by", str(user_id))\
                .is_("deleted_at", "null")\
                .order("created_at", desc=True)\
                .execute()
            return [Transcript(**transcript) for transcript in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get user transcripts: {str(e)}") from e

    async def get_video_transcript(self, video_id: UUID, access_token: str, refresh_token: str = None) -> Optional[Transcript]:
        """Get the transcript for a specific video using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('transcripts')\
                .select("*")\
                .eq("media_id", self._uuid_str(video_id))\
                .is_("deleted_at", "null")\
                .maybe_single()\
                .execute()
            return Transcript(**response.data) if response and response.data else None
        except Exception as e:
            raise DatabaseError(f"Failed to get video transcript: {str(e)}") from e

    async def get_transcript_with_media(self, transcript_id: UUID, access_token: str, refresh_token: str = None) -> Optional[Dict[str, Any]]:
        """Get transcript with related media information using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('transcripts')\
                .select("*, media(*)")\
                .eq("id", self._uuid_str(transcript_id))\
                .is_("deleted_at", "null")\
                .maybe_single()\
                .execute()
            return response.data if response and response.data else None
        except Exception as e:
            raise DatabaseError(f"Failed to get transcript with media: {str(e)}") from e

    # Backward compatibility method
    async def get_transcript_with_video(self, transcript_id: UUID) -> Optional[Dict[str, Any]]:
        """Get transcript with related video information (backward compatibility)"""
        return await self.get_transcript_with_media(transcript_id)

    # Client methods
    async def create_client_with_session(self, name: str, user_id: UUID, access_token: str, refresh_token: str) -> Client:
        """Create a new client using user's session (for RLS compliance) and add the creator as owner"""
        try:
            # Create client with user's session token for RLS compliance
            user_client = await acreate_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            
            # Set the user's session with both tokens
            await user_client.auth.set_session(access_token, refresh_token)
            
            # Verify session is set properly
            current_user = await user_client.auth.get_user()
            if not current_user or not current_user.user:
                raise AuthenticationError("Failed to set user session for client creation")
            
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
            raise DatabaseError(f"Failed to create client: {str(e)}") from e

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
            raise DatabaseError(f"Failed to create client: {str(e)}") from e
    
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
            raise DatabaseError(f"Failed to get user client: {str(e)}") from e
    
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
    
    async def get_client_users(self, user_id: UUID, access_token: str, refresh_token: str = None) -> List[ClientUser]:
        """Get all users in a client using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
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
            raise DatabaseError(f"Failed to get client users: {str(e)}") from e
    
    async def add_client_user(self, email: str, role: str, added_by: UUID) -> ClientUser:
        """Add a user to a client"""
        try:
            client = await self._get_client()
            # Get the client of the user adding
            user_client = await self.get_user_client(added_by)
            if not user_client:
                raise ValidationError("User is not associated with any client")
            
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
                raise ValidationError(f"User already belongs to client: {existing_client.name}")
            
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
            raise DatabaseError(f"Failed to add client user: {str(e)}") from e
    
    async def remove_client_user(self, user_id: UUID, removed_by: UUID, access_token: str, refresh_token: str = None) -> None:
        """Remove a user from a client using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            # Get the client of the user removing
            user_client = await self.get_user_client(removed_by)
            if not user_client:
                raise ValidationError("User is not associated with any client")
            
            # Soft delete the user from the client - audit fields handled by triggers
            await client.table('client_users')\
                .update({
                    "deleted_at": "now()"
                })\
                .eq("client_id", str(user_client.id))\
                .eq("user_id", str(user_id))\
                .is_("deleted_at", "null")\
                .execute()
        except Exception as e:
            raise DatabaseError(f"Failed to remove client user: {str(e)}") from e

    async def get_client_media(self, client_id: UUID, access_token: str, refresh_token: str = None) -> List[Media]:
        """Get all media for a client using user-authenticated client"""
        try:
            client = await self.create_user_authenticated_client(access_token, refresh_token)
            response = await client.table('media')\
                .select("*")\
                .eq("client_id", str(client_id))\
                .is_("deleted_at", "null")\
                .execute()
            return [Media(**media) for media in response.data]
        except Exception as e:
            raise DatabaseError(f"Failed to get client media: {str(e)}") from e

    # Backward compatibility method  
    async def get_client_videos(self, client_id: UUID, access_token: str, refresh_token: str = None) -> List[Video]:
        """Get videos for a client (backward compatibility)"""
        return await self.get_client_media(client_id, access_token, refresh_token)

    # File upload methods
    async def upload_file_with_smart_routing(
        self,
        file: UploadFile,
        bucket_name: str,
        storage_path: str,
        file_size: int,
        size_threshold: int = 6 * 1024 * 1024  # 6MB threshold
    ) -> str:
        """
        Smart file upload routing: standard upload for small files, TUS for large files
        
        Args:
            file: FastAPI UploadFile object
            bucket_name: Supabase storage bucket name
            storage_path: Path where file will be stored  
            file_size: Size of the file in bytes
            size_threshold: Size threshold for using TUS (default 6MB)
            
        Returns:
            str: Public URL of the uploaded file
        """
        try:
            if file_size <= size_threshold:
                self.logger.info(f"Using standard upload for {storage_path} ({file_size/1024/1024:.2f}MB)")
                return await self._upload_file_standard(file, bucket_name, storage_path)
            else:
                self.logger.info(f"Using TUS resumable upload for {storage_path} ({file_size/1024/1024:.2f}MB)")
                return await self._upload_file_tus(file, bucket_name, storage_path)
                
        except Exception as e:
            raise DatabaseError(f"Failed to upload file {storage_path}: {str(e)}") from e
    
    async def upload_file_from_path(
        self,
        file_path: Path,
        bucket_name: str,
        storage_path: str,
        content_type: str,
        file_size: int,
        size_threshold: int = 6 * 1024 * 1024  # 6MB threshold
    ) -> str:
        """
        Upload file directly from disk path with smart routing
        
        Args:
            file_path: Path to file on disk
            bucket_name: Supabase storage bucket name  
            storage_path: Path where file will be stored
            content_type: MIME type of the file
            file_size: Size of the file in bytes
            size_threshold: Size threshold for using TUS (default 6MB)
            
        Returns:
            str: Public URL of the uploaded file
        """
        try:
            if file_size <= size_threshold:
                self.logger.info(f"Using standard upload from path for {storage_path} ({file_size/1024/1024:.2f}MB)")
                return await self._upload_file_from_path_standard(file_path, bucket_name, storage_path, content_type)
            else:
                self.logger.info(f"Using TUS upload from path for {storage_path} ({file_size/1024/1024:.2f}MB)")
                return await self._upload_file_from_path_tus(file_path, bucket_name, storage_path, content_type, file_size)
                
        except Exception as e:
            raise DatabaseError(f"Failed to upload file from path {storage_path}: {str(e)}") from e
    
    async def _upload_file_from_path_standard(
        self,
        file_path: Path,
        bucket_name: str, 
        storage_path: str,
        content_type: str
    ) -> str:
        """Upload file from disk path using standard Supabase upload (for files ≤6MB)"""
        try:
            self.logger.info(f"Starting standard upload from {file_path} to {storage_path}")
            
            # Read file content directly
            with open(file_path, "rb") as file_content:
                file_data = file_content.read()
            
            # Upload to Supabase storage
            client = await self._get_service_client()
            response = await client.storage.from_(bucket_name).upload(
                storage_path,
                file_data,
                file_options={"content-type": content_type}
            )
            
            if hasattr(response, 'error') and response.error:
                raise DatabaseError(f"Supabase upload error: {response.error}")
            
            # Generate public URL
            public_url_response = await client.storage.from_(bucket_name).get_public_url(storage_path)
            return public_url_response
            
        except Exception as e:
            raise DatabaseError(f"Standard upload from path failed: {str(e)}") from e
    
    async def _upload_file_from_path_tus(
        self,
        file_path: Path,
        bucket_name: str,
        storage_path: str, 
        content_type: str,
        file_size: int
    ) -> str:
        """Upload large file from disk path using TUS resumable upload"""
        try:
            self.logger.info(f"Starting TUS upload from {file_path} to {storage_path}")
            
            # For TUS upload from path, use the same pattern as existing _upload_file_tus
            from app.services.tus_upload_service import tus_upload_service
            from fastapi import UploadFile
            import os
            
            # Create a file pointer that TUS can read from
            with open(file_path, "rb") as file_obj:
                # Create minimal UploadFile wrapper (TUS service expects this interface)
                temp_upload = UploadFile(
                    filename=os.path.basename(str(file_path)),
                    file=file_obj,
                    size=file_size
                )
                
                return await tus_upload_service.upload_file_resumable(
                    temp_upload,
                    bucket_name,
                    storage_path,
                    content_type
                )
            
        except Exception as e:
            raise DatabaseError(f"TUS upload from path failed: {str(e)}") from e
    
    async def _upload_file_standard(
        self,
        file: UploadFile,
        bucket_name: str,
        storage_path: str
    ) -> str:
        """Upload file using standard Supabase upload (for files ≤6MB)"""
        try:
            client = await self._get_service_client()
            
            # Read file content
            file.file.seek(0)
            file_content = file.file.read()
            
            # Upload to Supabase storage
            response = client.storage.from_(bucket_name).upload(
                storage_path,
                file_content,
                file_options={
                    "content-type": file.content_type,
                    "cache-control": "3600"
                }
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Supabase upload error: {response.error}")
            
            # Generate public URL
            public_url = client.storage.from_(bucket_name).get_public_url(storage_path)
            
            self.logger.info(f"Standard upload completed: {storage_path}")
            return public_url
            
        except Exception as e:
            self.logger.error(f"Standard upload failed for {storage_path}: {str(e)}")
            raise
    
    async def _upload_file_tus(
        self,
        file: UploadFile,
        bucket_name: str,
        storage_path: str
    ) -> str:
        """Upload file using TUS resumable upload (for files >6MB)"""
        try:
            from app.services.tus_upload_service import tus_upload_service
            
            # Use TUS service for large file upload
            public_url = await tus_upload_service.upload_file_resumable(
                file=file,
                bucket_name=bucket_name,
                storage_path=storage_path,
                content_type=file.content_type or "application/octet-stream"
            )
            
            self.logger.info(f"TUS upload completed: {storage_path}")
            return public_url
            
        except Exception as e:
            self.logger.error(f"TUS upload failed for {storage_path}: {str(e)}")
            raise

    async def create_presigned_upload_url(
        self,
        bucket: str,
        path: str,
        metadata: Dict[str, Any] = None,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Create a presigned URL for direct client uploads to Supabase Storage
        
        Args:
            bucket: Storage bucket name
            path: Storage path for the file
            metadata: Metadata to embed with the upload
            expires_in: URL expiration in seconds (default 1 hour)
            
        Returns:
            Dict containing upload_url and upload_fields for direct upload
        """
        try:
            client = await self._get_service_client()
            
            # Generate signed upload URL using correct Supabase SDK pattern
            storage_client = client.storage.from_(bucket)
            signed_url_response = await storage_client.create_signed_upload_url(path)
            
            # Handle different response formats from Supabase
            if isinstance(signed_url_response, dict):
                if 'error' in signed_url_response:
                    raise DatabaseError(f"Failed to create presigned URL: {signed_url_response['error']}")
                upload_url = signed_url_response.get('signedURL') or signed_url_response.get('url')
                upload_fields = signed_url_response.get('fields', {})
            else:
                # If response is a string, it's likely the URL directly
                upload_url = signed_url_response
                upload_fields = {}
            
            # Add metadata to upload fields if provided
            if metadata:
                # Supabase supports metadata through custom headers or form fields
                for key, value in metadata.items():
                    upload_fields[f"x-amz-meta-{key}"] = str(value)
            
            self.logger.info(f"Generated presigned upload URL for {path} (expires in {expires_in}s)")
            
            return {
                "url": upload_url,
                "fields": upload_fields
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create presigned upload URL: {str(e)}")
            raise DatabaseError(f"Presigned URL generation failed: {str(e)}") from e
    
    async def get_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Get a signed URL for downloading/accessing a file
        
        Args:
            bucket: Storage bucket name
            path: Storage path of the file
            expires_in: URL expiration in seconds (default 1 hour)
            
        Returns:
            Signed URL string
        """
        try:
            client = await self._get_service_client()
            
            signed_url_response = await client.storage.from_(bucket).create_signed_url(path, expires_in)
            
            if hasattr(signed_url_response, 'error') and signed_url_response.error:
                raise DatabaseError(f"Failed to create signed URL: {signed_url_response.error}")
            
            # Handle both dict and object response formats
            if hasattr(signed_url_response, 'get'):
                signed_url = signed_url_response.get('signedURL')
            else:
                signed_url = signed_url_response['signedURL']
            
            self.logger.info(f"Generated signed URL for {path} (expires in {expires_in}s)")
            return signed_url
            
        except Exception as e:
            self.logger.error(f"Failed to create signed URL: {str(e)}")
            raise DatabaseError(f"Signed URL generation failed: {str(e)}") from e

# Create a singleton instance
supabase_service = SupabaseService() 