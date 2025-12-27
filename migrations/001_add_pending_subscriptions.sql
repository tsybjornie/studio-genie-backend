-- Migration: Add pending_subscriptions table
-- Run this SQL directly on your PostgreSQL database

CREATE TABLE IF NOT EXISTS pending_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_subscription_id VARCHAR(255),
    plan_name VARCHAR(100) NOT NULL,
    price_id VARCHAR(255) NOT NULL,
    credits_to_award INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    claimed_at TIMESTAMP NULL,
    claimed_by_user_id UUID NULL,
    
    CONSTRAINT fk_claimed_by_user 
        FOREIGN KEY (claimed_by_user_id) 
        REFERENCES users(id) 
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_pending_subs_customer 
    ON pending_subscriptions(stripe_customer_id);

CREATE INDEX IF NOT EXISTS idx_pending_subs_claimed 
    ON pending_subscriptions(claimed_at) 
    WHERE claimed_at IS NULL;

-- Also need to add stripe_customer_id to users table if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer 
    ON users(stripe_customer_id);
