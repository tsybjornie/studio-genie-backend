-- ============================================================================
-- Credit Correction Migration
-- Fixes credits for all users who received incorrect amounts before fix
-- ============================================================================

-- STEP 1: Check affected users before fixing
SELECT 
    email, 
    subscription_plan, 
    credits AS current_credits,
    CASE 
        WHEN LOWER(subscription_plan) = 'starter' THEN 12
        WHEN LOWER(subscription_plan) = 'creator' THEN 36
        WHEN LOWER(subscription_plan) = 'pro' THEN 90
        ELSE credits
    END AS should_be_credits
FROM users 
WHERE subscription_status = 'active'
  AND subscription_plan IS NOT NULL
ORDER BY email;

-- STEP 2: Fix Starter plan users (should have 12 credits)
UPDATE users 
SET credits = 12 
WHERE subscription_status = 'active'
  AND LOWER(subscription_plan) = 'starter';

-- STEP 3: Fix Creator plan users (should have 36 credits)
UPDATE users 
SET credits = 36 
WHERE subscription_status = 'active'
  AND LOWER(subscription_plan) = 'creator';

-- STEP 4: Fix Pro plan users (should have 90 credits)
UPDATE users 
SET credits = 90 
WHERE subscription_status = 'active'
  AND LOWER(subscription_plan) = 'pro';

-- STEP 5: Also normalize plan names to lowercase for consistency
UPDATE users 
SET subscription_plan = LOWER(subscription_plan)
WHERE subscription_plan IS NOT NULL
  AND subscription_plan != LOWER(subscription_plan);

-- STEP 6: Verify correction
SELECT 
    subscription_plan, 
    COUNT(*) as user_count,
    credits
FROM users 
WHERE subscription_status = 'active'
GROUP BY subscription_plan, credits
ORDER BY subscription_plan;

-- Expected results:
-- starter  | user_count | 12
-- creator  | user_count | 36
-- pro      | user_count | 90
