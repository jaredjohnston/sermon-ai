# SermonAI Supabase Database Architecture Guide

**Created:** July 1, 2025  
**Purpose:** Complete database setup and security documentation for new developers and database administrators  
**Status:** Production-ready system with full RLS and audit implementation

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Database Schema](#database-schema)
3. [Authentication & Authorization Strategy](#authentication--authorization-strategy)
4. [Row Level Security (RLS) Policies](#row-level-security-rls-policies)
5. [Audit System & Triggers](#audit-system--triggers)
6. [Auth Role Decision Matrix](#auth-role-decision-matrix)
7. [Security Implementation Details](#security-implementation-details)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Verification Queries](#verification-queries)

---

## System Overview

### Architecture Philosophy
SermonAI implements a **multi-tenant SaaS architecture** using Supabase PostgreSQL with:
- **Client-based data isolation** (churches/organizations)
- **User-authenticated operations** for all user-initiated actions
- **Service role operations** for system/admin tasks
- **Database-level security** through RLS policies
- **Comprehensive audit trails** for compliance and debugging

### Key Design Principles
1. **Security by Default**: All data access controlled by RLS policies
2. **Audit Everything**: Every operation tracked with user attribution
3. **Multi-tenant Isolation**: Churches cannot see each other's data
4. **Auth Context Preservation**: Always maintain user context in operations

---

## Database Schema

### Core Tables

#### 1. **Authentication & User Management**
```sql
-- User profiles (extends Supabase auth.users)
user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE REFERENCES auth.users(id),
    first_name TEXT,
    last_name TEXT,
    country TEXT,
    phone TEXT,
    bio TEXT,
    avatar_url TEXT,
    -- Audit fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID NOT NULL REFERENCES auth.users(id),
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES auth.users(id)
)

-- Organizations/Churches
clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL CHECK (length >= 2 AND length <= 100),
    subscription_status subscription_status DEFAULT 'trial',
    -- Audit fields (same pattern)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES auth.users(id),
    updated_by UUID NOT NULL REFERENCES auth.users(id),
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES auth.users(id)
)

-- User-Organization relationships
client_users (
    client_id UUID NOT NULL REFERENCES clients(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role user_role NOT NULL DEFAULT 'member', -- owner, admin, member
    -- Audit fields (same pattern)
    PRIMARY KEY (client_id, user_id)
)
```

#### 2. **Content & Media**
```sql
-- Media files (videos, audio, documents)
media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL UNIQUE,
    content_type TEXT NOT NULL, -- video/*, audio/*, text/*, application/*
    size_bytes BIGINT NOT NULL CHECK (size_bytes > 0),
    metadata JSONB DEFAULT '{}',
    user_id UUID NOT NULL REFERENCES auth.users(id), -- Uploader
    -- Audit fields (same pattern)
)

-- Transcription results
transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    video_id UUID NOT NULL REFERENCES media(id), -- Historical name
    status transcript_status DEFAULT 'processing', -- processing, completed, failed
    raw_transcript JSONB, -- Direct from Deepgram
    processed_transcript JSONB, -- Cleaned/formatted
    error_message TEXT,
    request_id TEXT, -- Deepgram request tracking
    user_id UUID NOT NULL REFERENCES auth.users(id), -- Requester
    metadata JSONB DEFAULT '{}',
    -- Audit fields (same pattern)
)
```

#### 3. **AI Content Generation**
```sql
-- Content templates (prompts for AI generation)
content_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    name TEXT NOT NULL,
    description TEXT,
    content_type_name TEXT NOT NULL, -- "social_post", "sermon_outline", etc.
    structured_prompt TEXT NOT NULL, -- AI prompt template
    example_content JSONB DEFAULT '[]',
    status template_status DEFAULT 'active', -- active, inactive, archived
    model_settings JSONB DEFAULT '{"model": "gpt-4o", "max_tokens": 2000, "temperature": 0.7}',
    -- Audit fields (same pattern)
)

-- Generated content from AI
generated_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    transcript_id UUID NOT NULL REFERENCES transcripts(id),
    template_id UUID NOT NULL REFERENCES content_templates(id),
    content TEXT NOT NULL, -- AI-generated output
    content_metadata JSONB DEFAULT '{}',
    generation_settings JSONB DEFAULT '{}',
    generation_cost_cents INTEGER,
    generation_duration_ms INTEGER,
    user_edits_count INTEGER DEFAULT 0,
    last_edited_at TIMESTAMPTZ,
    -- Audit fields (same pattern)
)
```

### Custom Types
```sql
-- User roles within organizations
CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member');

-- Subscription status
CREATE TYPE subscription_status AS ENUM ('trial', 'active', 'cancelled', 'past_due');

-- Transcript processing status
CREATE TYPE transcript_status AS ENUM ('processing', 'completed', 'failed');

-- Template status
CREATE TYPE template_status AS ENUM ('active', 'inactive', 'archived');
```

---

## Authentication & Authorization Strategy

### Three-Tier Auth System

#### 1. **Anon Key (Public Operations)**
- **Purpose**: Public endpoints and user-authenticated operations
- **Usage**: Authentication flows, user-initiated CRUD operations
- **Context**: Respects RLS policies, provides user context via `auth.uid()`

```python
# Usage example
client = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
client.options.headers["Authorization"] = f"Bearer {access_token}"
response = await client.table('media').select('*').execute()
```

#### 2. **Service Role Key (Admin Operations)**
- **Purpose**: System-level operations, bypasses RLS
- **Usage**: Admin tasks, background processes, webhook handling
- **Context**: No user context (`auth.uid()` returns NULL)

```python
# Usage example
client = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
response = await client.table('system_logs').insert(log_data).execute()
```

#### 3. **User-Authenticated Client (Hybrid)**
- **Purpose**: User operations with proper audit trails
- **Usage**: User-initiated actions that need user context for RLS and audit
- **Context**: Provides real user ID via `auth.uid()`

```python
# Usage example
client = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
await client.auth.set_session(access_token, refresh_token)
response = await client.table('content_templates').insert(template_data).execute()
```

### Auth Role Decision Tree

```
Is this operation initiated by a user?
├─ YES: Use User-Authenticated Client
│   ├─ User viewing/editing their own data
│   ├─ Operations that need audit trails
│   └─ Operations that should respect RLS policies
│
└─ NO: What type of system operation?
    ├─ Admin operation? → Use Service Role
    ├─ Background process? → Use Service Role
    ├─ Webhook callback? → Use Service Role
    ├─ Storage operation? → Use Service Role
    └─ Public auth (signup/signin)? → Use Anon Key
```

---

## Row Level Security (RLS) Policies

### Policy Status: **ENABLED** on All Tables

#### 1. **Clients Table Policies**
```sql
-- Policy 1: Users can create organizations (INSERT)
CREATE POLICY "Users can create organizations" ON clients
    FOR INSERT 
    TO authenticated, service_role
    WITH CHECK (
        auth.uid() IS NOT NULL OR auth.role() = 'service_role'
    );

-- Policy 2: Service role can create clients (INSERT)
CREATE POLICY "Service role can create clients" ON clients
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Policy 3: Users can view their organizations (SELECT)
CREATE POLICY "Users can view their organizations" ON clients
    FOR SELECT
    TO authenticated
    USING (id IN (
        SELECT client_id 
        FROM client_users 
        WHERE user_id = auth.uid() 
        AND deleted_at IS NULL
    ));
```

#### 2. **User Profiles Policies**
```sql
-- Users can view their own profile
CREATE POLICY "Users can view their own profile" ON user_profiles
    FOR SELECT
    TO public
    USING (user_id = auth.uid());

-- Users can update their own profile
CREATE POLICY "Users can update their own profile" ON user_profiles
    FOR UPDATE
    TO public
    USING (user_id = auth.uid());

-- Users can insert their own profile (with service role exception)
CREATE POLICY "Users can insert their own profile" ON user_profiles
    FOR INSERT
    TO public
    WITH CHECK (
        (user_id = auth.uid()) OR (auth.role() = 'service_role')
    );

-- Client members can view teammate profiles
CREATE POLICY "Client members can view teammate profiles" ON user_profiles
    FOR SELECT
    TO public
    USING (user_id IN (
        SELECT cu.user_id
        FROM client_users cu
        WHERE cu.client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND cu.deleted_at IS NULL
    ));
```

#### 3. **Client Users Policies**
```sql
-- Client owners can manage users
CREATE POLICY "Client owners can manage users" ON client_users
    FOR ALL
    TO authenticated
    USING (
        deleted_at IS NULL 
        AND is_client_owner(auth.uid(), client_id)
    )
    WITH CHECK (
        deleted_at IS NULL 
        AND is_client_owner(auth.uid(), client_id)
    );

-- Users can view active members of their client
CREATE POLICY "Users can view active members of their active client" ON client_users
    FOR SELECT
    TO authenticated
    USING (
        deleted_at IS NULL 
        AND is_active_member(auth.uid(), client_id)
    );
```

#### 4. **Media Table Policies**
```sql
-- Users can manage their own media
CREATE POLICY "Users can manage their own videos" ON media
    FOR ALL
    TO authenticated
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND created_by = auth.uid()
        AND deleted_at IS NULL
    );

-- Users can view all client media
CREATE POLICY "Users can view active videos from their active client" ON media
    FOR SELECT
    TO authenticated
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );
```

#### 5. **Transcripts Policies**
```sql
-- Users can manage their own transcripts
CREATE POLICY "Users can manage their own transcripts" ON transcripts
    FOR ALL
    TO authenticated
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND created_by = auth.uid()
        AND deleted_at IS NULL
    );

-- Users can view all client transcripts
CREATE POLICY "Users can view active transcripts from their active client" ON transcripts
    FOR SELECT
    TO authenticated
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );
```

#### 6. **Content Templates Policies**
```sql
-- Shared within organization (collaborative)
CREATE POLICY "Users can manage templates for their client" ON content_templates
    FOR ALL
    TO public
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can view active templates from their client" ON content_templates
    FOR SELECT
    TO public
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );
```

#### 7. **Generated Content Policies**
```sql
-- Shared within organization (collaborative)
CREATE POLICY "Users can manage generated content for their client" ON generated_content
    FOR ALL
    TO public
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );

CREATE POLICY "Users can view generated content from their client" ON generated_content
    FOR SELECT
    TO public
    USING (
        client_id IN (
            SELECT client_id
            FROM client_users
            WHERE user_id = auth.uid()
            AND deleted_at IS NULL
        )
        AND deleted_at IS NULL
    );
```

### Helper Functions
```sql
-- Check if user is client owner
CREATE OR REPLACE FUNCTION is_client_owner(user_uuid UUID, client_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM client_users
        WHERE user_id = user_uuid
        AND client_id = client_uuid
        AND role = 'owner'
        AND deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Check if user is active member
CREATE OR REPLACE FUNCTION is_active_member(user_uuid UUID, client_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM client_users
        WHERE user_id = user_uuid
        AND client_id = client_uuid
        AND deleted_at IS NULL
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## Audit System & Triggers

### System User for Service Operations
```sql
-- Special system user for service role operations
INSERT INTO auth.users (
    id,
    email,
    created_at,
    updated_at,
    email_confirmed_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role
) VALUES (
    '00000000-0000-0000-0000-000000000000'::uuid,
    'system@sermonai.internal',
    NOW(),
    NOW(),
    NOW(),
    '{"provider":"system","providers":["system"]}'::jsonb,
    '{"name":"System User","role":"system"}'::jsonb,
    false,
    'authenticated'
);
```

### Universal Audit Trigger Function
```sql
CREATE OR REPLACE FUNCTION handle_audit_fields()
RETURNS TRIGGER AS $$
DECLARE
    current_user_id UUID;
    system_user_id UUID := '00000000-0000-0000-0000-000000000000'::UUID;
BEGIN
    -- Get current user ID from auth.uid(), fallback to system user for service role operations
    current_user_id := COALESCE(auth.uid(), system_user_id);
    
    IF (TG_OP = 'INSERT') THEN
        -- Set all audit fields for new records
        NEW.created_at = TIMEZONE('utc', NOW());
        NEW.updated_at = TIMEZONE('utc', NOW());
        NEW.created_by = current_user_id;
        NEW.updated_by = current_user_id;
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Only update the "updated" fields, preserve original created_* fields
        NEW.updated_at = TIMEZONE('utc', NOW());
        NEW.updated_by = current_user_id;
        -- Explicitly preserve created_at and created_by
        NEW.created_at = OLD.created_at;
        NEW.created_by = OLD.created_by;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Triggers Applied to All Tables
```sql
-- Applied to: clients, client_users, user_profiles, media, transcripts, content_templates, generated_content

-- Example for clients table
CREATE TRIGGER clients_audit_trigger
    BEFORE INSERT OR UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION handle_audit_fields();
```

### Audit Field Patterns
- **User Operations**: `created_by` = real user UUID, `updated_by` = real user UUID
- **Service Operations**: `created_by` = system user UUID (`00000000-0000-0000-0000-000000000000`)
- **Mixed Operations**: Updates preserve original `created_by`, set new `updated_by`

---

## Auth Role Decision Matrix

### Service Method Categories

#### ✅ **User-Authenticated Methods** (require access_token)
```python
# User Profile Operations
async def get_user_profile(user_id, access_token, refresh_token=None)
async def update_user_profile(user_id, updates, access_token, refresh_token=None)

# Media Access Operations  
async def get_user_media(user_id, access_token, refresh_token=None)
async def get_client_media(client_id, access_token, refresh_token=None)

# Team Operations
async def create_team(team, user_id, access_token, refresh_token=None)
async def get_user_teams(user_id, access_token, refresh_token=None)

# Transcript Operations
async def get_transcript(transcript_id, access_token, refresh_token=None)
async def update_transcript(transcript_id, updates, user_id, access_token, refresh_token=None)
async def get_client_transcripts(client_id, access_token, refresh_token=None)
async def get_user_transcripts(user_id, access_token, refresh_token=None)

# Client User Management
async def get_client_users(user_id, access_token, refresh_token=None)
async def remove_client_user(user_id, removed_by, access_token, refresh_token=None)

# Content Templates (shared within client)
async def create_template(template, user_id, access_token, refresh_token=None)
async def get_client_templates(client_id, access_token, refresh_token=None)
```

#### 🔧 **Service Role Methods** (system operations)
```python
# Authentication & Admin Operations
async def get_user(user_id) -> User                    # Auth admin API call
async def add_client_user(email, role, added_by)       # Admin user management  
async def _is_admin_user(user_id) -> bool             # Admin permission check

# System Operations (Background Processes)
async def create_media(media, user_id)                 # System-level creation
async def create_transcript(transcript, user_id)       # Background processing
async def create_user_profile(profile, user_id)        # Service-level creation
async def create_organization(org_name, session)       # Organization creation during signup

# Storage Operations
async def upload_file_with_smart_routing(...)          # Storage requires elevated permissions

# Webhook Operations
async def update_transcript_system(transcript_id, updates, user_id)  # Webhook callbacks
```

### API Endpoint Patterns

#### AuthContext Pattern (Recommended)
```python
from app.middleware.auth import get_auth_context, AuthContext

@router.post("/templates")
async def create_template(
    template: ContentTemplateCreate,
    auth: AuthContext = Depends(get_auth_context)  # Provides user + access_token
):
    created_template = await template_service.create_template(
        template, auth.user.id, auth.access_token
    )
    return created_template
```

#### Legacy Pattern (Backward Compatible)
```python
from app.middleware.auth import get_current_user

@router.get("/profile")  
async def get_profile(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
```

---

## Security Implementation Details

### Multi-Tenant Isolation Strategy
1. **Client-based separation**: All business data includes `client_id`
2. **RLS enforcement**: Database-level policies prevent cross-client access
3. **User-authenticated operations**: Always use real user context for data access
4. **Service role restrictions**: Limited to genuine system operations

### Data Access Patterns
```sql
-- Standard client isolation pattern used throughout RLS policies
client_id IN (
    SELECT client_id
    FROM client_users
    WHERE user_id = auth.uid()
    AND deleted_at IS NULL
)
```

### Ownership vs Sharing Models
- **Individual Ownership**: `media`, `transcripts` (user owns what they create)
- **Shared within Client**: `content_templates`, `generated_content` (collaborative)
- **Client Membership**: `client_users` (owner/admin control)

### Soft Delete Implementation
- All tables include `deleted_at` and `deleted_by` fields
- RLS policies always check `deleted_at IS NULL`
- Enables data recovery and audit trails

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue: "Field 'model_settings' has conflict with protected namespace 'model_'"
**Solution**: Add to Pydantic model:
```python
class YourModel(BaseModel):
    model_config = {"protected_namespaces": ()}
```

#### Issue: Audit fields (created_by, updated_by) are NULL
**Cause**: Using service role client for user operations  
**Solution**: Convert to user-authenticated client and pass access_token

#### Issue: "User does not belong to any client" errors
**Cause**: User context is lost in service role operations  
**Solution**: Use user-authenticated client to maintain user context

#### Issue: RLS policy violations during signup
**Cause**: Session timing or auth context issues  
**Solution**: Ensure service role policies exist for system operations

#### Issue: 401 Unauthorized errors
**Cause**: Missing or invalid Bearer token  
**Solution**: Verify `headers = {"Authorization": f"Bearer {access_token}"}`

### Debugging Queries

#### Check Auth Context
```sql
SELECT 
    auth.uid() as current_user_id,
    auth.role() as current_role,
    CASE 
        WHEN auth.uid() IS NULL THEN 'Service Role Context'
        ELSE 'User Context'
    END as auth_context;
```

#### Verify RLS Status
```sql
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    CASE WHEN rowsecurity THEN '✅ ENABLED' ELSE '❌ DISABLED' END as status
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
```

#### Check Audit Triggers
```sql
SELECT 
    event_object_table as table_name,
    trigger_name,
    '✅ INSTALLED' as status
FROM information_schema.triggers 
WHERE event_object_schema = 'public' 
AND trigger_name LIKE '%audit%'
ORDER BY event_object_table;
```

#### Test User Isolation
```sql
-- Run as authenticated user to test isolation
SELECT 
    'Clients I can see' as test,
    COUNT(*) as count
FROM clients
WHERE id IN (
    SELECT client_id
    FROM client_users
    WHERE user_id = auth.uid()
    AND deleted_at IS NULL
);
```

---

## Verification Queries

### Complete System Health Check
```sql
-- 1. Check system user exists
SELECT 
    id,
    email,
    CASE WHEN id = '00000000-0000-0000-0000-000000000000' THEN '✅ SYSTEM USER' ELSE '👤 REGULAR USER' END as user_type
FROM auth.users 
WHERE id = '00000000-0000-0000-0000-000000000000';

-- 2. Verify RLS enabled on all tables
SELECT 
    tablename,
    rowsecurity,
    CASE WHEN rowsecurity THEN '✅ RLS ENABLED' ELSE '❌ RLS DISABLED' END as status
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN ('clients', 'client_users', 'user_profiles', 'media', 'transcripts', 'content_templates', 'generated_content')
ORDER BY tablename;

-- 3. Count policies per table
SELECT 
    tablename,
    COUNT(*) as policy_count,
    CASE WHEN COUNT(*) > 0 THEN '✅ HAS POLICIES' ELSE '❌ NO POLICIES' END as status
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- 4. Verify audit triggers installed
SELECT 
    COUNT(*) as total_audit_triggers,
    CASE WHEN COUNT(*) >= 7 THEN '✅ ALL TABLES COVERED' ELSE '❌ MISSING TRIGGERS' END as status
FROM information_schema.triggers 
WHERE event_object_schema = 'public' 
AND trigger_name LIKE '%audit%';

-- 5. Test audit trigger functionality
DO $$
DECLARE
    test_client_id UUID;
BEGIN
    INSERT INTO clients (name) VALUES ('System Test - Can Delete') RETURNING id INTO test_client_id;
    
    IF EXISTS (
        SELECT 1 FROM clients 
        WHERE id = test_client_id 
        AND created_by IS NOT NULL 
        AND updated_by IS NOT NULL
    ) THEN
        RAISE NOTICE '✅ Audit triggers working correctly';
        DELETE FROM clients WHERE id = test_client_id;
    ELSE
        RAISE EXCEPTION '❌ Audit triggers not working';
    END IF;
END $$;
```

### Performance Monitoring
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Monitor RLS policy performance
SELECT 
    schemaname,
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, cmd;
```

---

## Production Checklist

### Security Verification ✅
- [ ] RLS enabled on all business tables
- [ ] System user created for service operations
- [ ] Audit triggers installed and tested
- [ ] Multi-tenant isolation verified
- [ ] Auth role separation implemented

### Performance Optimization ✅
- [ ] Appropriate indexes on foreign keys
- [ ] Client isolation queries optimized
- [ ] RLS policy efficiency verified
- [ ] Audit trigger performance acceptable

### Operational Readiness ✅
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Documentation complete and current
- [ ] Team training completed
- [ ] Troubleshooting procedures documented

---

## Maintenance Notes

### Regular Tasks
1. **Monitor audit trail growth** - Archive old audit data as needed
2. **Review RLS policy performance** - Optimize queries if needed
3. **Verify system user integrity** - Ensure system user remains valid
4. **Test multi-tenant isolation** - Regular verification of data separation

### Schema Changes
1. **New tables**: Apply audit triggers and RLS policies
2. **Column additions**: Update audit triggers if audit fields added
3. **Policy changes**: Test thoroughly in staging environment
4. **Migration safety**: Always verify RLS doesn't break migrations

### Security Reviews
1. **Quarterly RLS policy review** - Ensure policies match business requirements
2. **Auth role audit** - Verify service vs user operations remain properly categorized
3. **Access pattern analysis** - Monitor for unusual data access patterns
4. **Compliance verification** - Ensure audit trails meet regulatory requirements

---

**End of Guide**  
*This document represents the production-ready state of the SermonAI database as of July 1, 2025. All security features have been implemented and tested.*

**Key Contributors**: Database architecture designed and implemented with comprehensive RLS policies, audit systems, and multi-tenant security patterns.