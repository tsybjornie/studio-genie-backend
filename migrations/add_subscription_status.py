"""
Add subscription status column to users table
Migration for subscription gating implementation
"""

def up():
    """Add has_active_subscription column and index"""
    return """
    -- Add subscription status column
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS has_active_subscription BOOLEAN DEFAULT FALSE;
    
    -- Add index for fast subscription checks
    CREATE INDEX IF NOT EXISTS idx_users_subscription 
    ON users(has_active_subscription);
    
    -- Add stripe_subscription_id if not exists
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
    """

def down():
    """Rollback subscription column"""
    return """
    DROP INDEX IF EXISTS idx_users_subscription;
    ALTER TABLE users DROP COLUMN IF EXISTS has_active_subscription;
    ALTER TABLE users DROP COLUMN IF EXISTS stripe_subscription_id;
    """
