# ADR-003: Automatic User Provisioning System with Email Confirmation Triggers

**Status:** Accepted  
**Date:** 2025-07-24  
**Decision Makers:** Development Team  
**Technical Story:** Implement reliable, automatic user provisioning system that creates user profiles and organizations when users confirm their email addresses.

## Context

The existing auth system had a critical flaw: users were manually provisioned during the signup API call, leading to several problems:

1. **Synchronous Bottleneck**: Complex provisioning logic in signup endpoint caused slow API responses
2. **Single Point of Failure**: If organization creation failed, users were left in partial signup state
3. **Ghost Users**: Unconfirmed email addresses were getting full provisioning
4. **No Retry Logic**: Failed provisioning left users in inconsistent state
5. **Security Vulnerabilities**: Using `getSession()` instead of `getUser()` in server-side code

## Decision

We implemented an **automatic user provisioning system** using Supabase database triggers that activates when users confirm their email addresses.

### Core Architecture

```
User Signup → Email Confirmation → Database Trigger → Automatic Provisioning
```

## Implementation Details

### 1. Authentication Stack

**Technology Choices:**
- **Supabase Auth**: JWT + refresh token strategy with PKCE flow
- **@supabase/ssr**: Server-side rendering support for Next.js App Router
- **Cookie Storage**: Regular cookies (not httpOnly) per Supabase recommendations
- **Multi-tenant Architecture**: RLS-based data isolation

**Client Configuration:**
- `createBrowserClient()`: Client-side auth operations
- `createServerClient()`: Server-side auth with cookie handling
- `createClient()`: Middleware for request/response processing

### 2. Database Trigger System

**Core Function (`handle_email_confirmed`):**
```sql
CREATE OR REPLACE FUNCTION public.handle_email_confirmed()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
    -- Only proceed if email was just confirmed (NULL -> timestamp)
    IF OLD.email_confirmed_at IS NULL AND NEW.email_confirmed_at IS NOT NULL THEN
        -- Create user profile, organization, and association
        -- All operations in atomic transaction
    END IF;
    RETURN NEW;
END;
$$;
```

**Trigger Definition:**
```sql
CREATE TRIGGER on_auth_user_email_confirmed
    AFTER UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_email_confirmed();
```

### 3. Security Implementation

**Server-Side Security:**
- **Middleware**: Uses `getUser()` for auth validation (prevents spoofing)
- **Protected Layout**: Server-side user verification
- **RLS Policies**: Multi-tenant data isolation

**Auth Context:**
- **Client-Side**: React Context using `getSession()` (acceptable for UI state)
- **Server-Side**: Always `getUser()` for security-critical operations

### 4. User Provisioning Flow

**Signup Process:**
1. User submits signup form with metadata
2. Frontend calls `supabase.auth.signUp()` with user data in `options.data`
3. Supabase creates `auth.users` record with `email_confirmed_at = NULL`
4. User receives confirmation email

**Email Confirmation Process:**
1. User clicks email confirmation link
2. Supabase updates `email_confirmed_at` with timestamp
3. Database trigger detects the change (NULL → timestamp)
4. Trigger extracts metadata from `raw_user_meta_data`
5. Atomic transaction creates:
   - `user_profiles` record
   - `clients` record (organization)
   - `client_users` association (user as owner)

**Dashboard Access:**
1. User redirected to frontend with confirmation code
2. AuthProvider exchanges code for session tokens
3. Middleware validates user has `email_confirmed_at`
4. User accesses dashboard with fully provisioned account

## Rationale

### Why Database Triggers Over Alternatives

**Alternatives Considered:**

1. **Database Webhooks**: More observable but adds HTTP overhead
2. **Edge Functions**: Good for complex logic but adds latency
3. **Client-Side Post-Auth**: Simple but unreliable (user can close browser)
4. **Manual API Provisioning**: Current approach - too many failure points

**Why Triggers Won:**
- **Atomic Operations**: Database transaction ensures all-or-nothing provisioning
- **Reliability**: Can't be bypassed or forgotten
- **Performance**: No HTTP calls or external dependencies
- **Consistency**: Works with any signup method (API, admin, future OAuth)
- **Simplicity**: Less moving parts than webhook/Edge Function approaches

### Why Email Confirmation First

- **Security**: Only confirmed humans get resources
- **Resource Efficiency**: No wasted database records for abandoned signups
- **Compliance**: Email verification is industry standard
- **User Experience**: Clear activation flow matches user expectations

### Why Supabase Auth

- **Battle-Tested**: Handles JWT refresh, security, edge cases
- **SSR Support**: Native Next.js App Router integration
- **Multi-Tenant Ready**: Built-in RLS and user management
- **Conventional**: Standard patterns, extensive documentation

## Consequences

### Positive

✅ **Reliability**: Atomic provisioning eliminates partial signup states  
✅ **Performance**: Fast signup API responses (no sync provisioning)  
✅ **Security**: Email-confirmed users only, proper server-side auth validation  
✅ **Maintainability**: Simple trigger logic, fewer failure points  
✅ **Scalability**: Database-level automation, no API bottlenecks  
✅ **Consistency**: Works across all signup methods  

### Negative

⚠️ **Debugging Complexity**: Trigger failures require database log analysis  
⚠️ **Testing Overhead**: Email confirmation required for integration tests  
⚠️ **Migration Risk**: Trigger changes require careful database migrations  

### Neutral

🔄 **Idempotency**: System handles duplicate confirmations gracefully  
🔄 **Audit Trail**: All operations logged with proper user attribution  
🔄 **Error Handling**: Trigger failures don't prevent email confirmation  

## Technical Artifacts

### Key Files Created/Modified

**Database:**
- `backend/migrations/10_user_provisioning_trigger.sql`: Core trigger implementation

**Frontend:**
- `frontend/lib/supabase/*`: Supabase client configurations
- `frontend/components/providers/AuthProvider.tsx`: React auth context
- `frontend/app/(auth)/*`: Authentication pages
- `frontend/app/(protected)/*`: Protected route structure
- `frontend/middleware.ts`: Route protection and redirects

**Backend:**
- `backend/app/api/endpoints/auth.py`: Simplified signup endpoint

### Security Configurations

- **RLS Policies**: Multi-tenant data isolation
- **Function Security**: `SECURITY DEFINER SET search_path = ''`
- **Auth Validation**: `getUser()` for server-side operations
- **Metadata Handling**: Secure extraction from `raw_user_meta_data`

## Monitoring & Observability

**Success Metrics:**
- User signup completion rate
- Email confirmation to dashboard access time
- Provisioning success rate (no partial accounts)

**Key Logs to Monitor:**
- Supabase Auth logs for confirmation events
- Database function logs for provisioning success/failure
- Application logs for auth flow completion

**Alerting Triggers:**
- Provisioning function failures
- High email confirmation bounce rates
- Auth token validation errors

## Future Considerations

### Potential Enhancements

1. **Background Job Retry**: For failed provisioning attempts
2. **Admin Provisioning Override**: Manual user activation for edge cases
3. **OAuth Integration**: Extend trigger to handle social logins
4. **Advanced Organizations**: Support for invitations and team management

### Migration Paths

1. **Rollback Strategy**: Drop trigger, restore manual provisioning endpoint
2. **Trigger Updates**: Careful schema migrations with backup/restore procedures
3. **Multi-Environment**: Consistent trigger deployment across dev/staging/prod

---

**This ADR documents the shift from manual, synchronous user provisioning to an automatic, trigger-based system that activates on email confirmation. The implementation prioritizes reliability, security, and user experience while maintaining simplicity and conventional patterns.**