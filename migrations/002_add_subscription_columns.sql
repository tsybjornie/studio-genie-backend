-- Migration: Add subscription_status and subscription_plan columns to users table
-- Run this SQL directly on your Render PostgreSQL database

-- Add subscription_status column (default 'inactive')
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive';

-- Add subscription_plan column (nullable)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_plan TEXT;

-- Add stripe_customer_id if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) UNIQUE;

-- Add stripe_subscription_id if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_subscription_status 
ON users(subscription_status);

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer 
ON users(stripe_customer_id);

-- Verify columns were added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('subscription_status', 'subscription_plan', 'stripe_customer_id', 'stripe_subscription_id');
