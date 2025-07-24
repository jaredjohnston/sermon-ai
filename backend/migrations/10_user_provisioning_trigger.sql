-- User Provisioning Trigger for Email Confirmation
-- This trigger automatically creates user profile, organization, and associations
-- when a user confirms their email address (email_confirmed_at changes from NULL to timestamp)

-- Create the user provisioning function
CREATE OR REPLACE FUNCTION public.handle_email_confirmed()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
DECLARE
    new_client_id UUID;
    organization_name TEXT;
    user_first_name TEXT;
    user_last_name TEXT;
    user_country TEXT;
BEGIN
    -- Only proceed if email was just confirmed (NULL -> timestamp)
    IF OLD.email_confirmed_at IS NULL AND NEW.email_confirmed_at IS NOT NULL THEN
        
        -- Log the provisioning attempt
        RAISE LOG 'Starting user provisioning for user_id: %, email: %', NEW.id, NEW.email;
        
        -- Extract metadata from auth user
        organization_name := NEW.raw_user_meta_data ->> 'organization_name';
        user_first_name := NEW.raw_user_meta_data ->> 'first_name';
        user_last_name := NEW.raw_user_meta_data ->> 'last_name';
        user_country := NEW.raw_user_meta_data ->> 'country';
        
        -- Validate required fields
        IF organization_name IS NULL OR LENGTH(TRIM(organization_name)) < 2 THEN
            RAISE EXCEPTION 'Missing or invalid organization_name in user metadata for user %', NEW.id;
        END IF;
        
        IF user_first_name IS NULL OR LENGTH(TRIM(user_first_name)) < 1 THEN
            RAISE EXCEPTION 'Missing or invalid first_name in user metadata for user %', NEW.id;
        END IF;
        
        IF user_last_name IS NULL OR LENGTH(TRIM(user_last_name)) < 1 THEN
            RAISE EXCEPTION 'Missing or invalid last_name in user metadata for user %', NEW.id;
        END IF;
        
        -- Check if user is already provisioned (idempotency)
        IF EXISTS (SELECT 1 FROM public.user_profiles WHERE user_id = NEW.id AND deleted_at IS NULL) THEN
            RAISE LOG 'User % already provisioned, skipping', NEW.id;
            RETURN NEW;
        END IF;
        
        -- Start transaction block for atomic operations
        BEGIN
            -- 1. Create user profile
            INSERT INTO public.user_profiles (
                user_id,
                first_name,
                last_name,
                country,
                created_by,
                updated_by
            ) VALUES (
                NEW.id,
                TRIM(user_first_name),
                TRIM(user_last_name),
                TRIM(user_country),
                NEW.id,  -- User creates their own profile
                NEW.id
            );
            
            RAISE LOG 'Created user_profile for user %', NEW.id;
            
            -- 2. Create organization (client)
            INSERT INTO public.clients (
                name,
                subscription_status,
                created_by,
                updated_by
            ) VALUES (
                TRIM(organization_name),
                'trial',  -- Default to trial subscription
                NEW.id,
                NEW.id
            ) RETURNING id INTO new_client_id;
            
            RAISE LOG 'Created client % for user %', new_client_id, NEW.id;
            
            -- 3. Associate user with organization as owner
            INSERT INTO public.client_users (
                client_id,
                user_id,
                role,
                created_by,
                updated_by
            ) VALUES (
                new_client_id,
                NEW.id,
                'owner',
                NEW.id,
                NEW.id
            );
            
            RAISE LOG 'Associated user % as owner of client %', NEW.id, new_client_id;
            
            -- Success log
            RAISE LOG 'Successfully provisioned user % with client % (%)', NEW.id, new_client_id, organization_name;
            
        EXCEPTION
            WHEN OTHERS THEN
                -- Log the error but don't prevent email confirmation
                RAISE LOG 'User provisioning failed for user %: % - %', NEW.id, SQLSTATE, SQLERRM;
                -- Re-raise the exception to rollback the transaction
                RAISE;
        END;
        
    END IF;
    
    RETURN NEW;
END;
$$;

-- Create the trigger on auth.users for UPDATE events
CREATE TRIGGER on_auth_user_email_confirmed
    AFTER UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_email_confirmed();

-- Grant necessary permissions (if needed)
-- The function uses SECURITY DEFINER so it runs with the function owner's privileges

-- Create rollback instructions (commented out)
/*
-- To rollback this migration:
-- DROP TRIGGER IF EXISTS on_auth_user_email_confirmed ON auth.users;
-- DROP FUNCTION IF EXISTS public.handle_email_confirmed();
*/

-- Add helpful comment
COMMENT ON FUNCTION public.handle_email_confirmed() IS 
'Automatically provisions users (creates profile, organization, and association) when they confirm their email address. Triggered by auth.users UPDATE when email_confirmed_at changes from NULL to timestamp.';

COMMENT ON TRIGGER on_auth_user_email_confirmed ON auth.users IS 
'Triggers user provisioning when email is confirmed via handle_email_confirmed() function.';