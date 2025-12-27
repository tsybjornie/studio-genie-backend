#!/usr/bin/env python3
"""
Verify that .env files are clean and match Render configuration.
"""
import os
from pathlib import Path

# Allowed JWT variables (ONLY THESE 3)
ALLOWED_JWT_VARS = {
    'SECRET_KEY',
    'ALGORITHM',
    'ACCESS_TOKEN_EXPIRE_MINUTES'
}

# Forbidden JWT variables (must be deleted)
FORBIDDEN_JWT_VARS = {
    'JWT_SECRET',
    'JWT_REFRESH_SECRET',
    'JWT_EXPIRES_IN',
    'JWT_REFRESH_EXPIRES_IN',
    'JWT_ACCESS_SECRET',
    'JWT_REFRESH_EXPIRES_IN_DAYS'
}

def check_env_file(filepath, name):
    """Check a .env file for problematic JWT variables."""
    print(f"\n{'='*60}")
    print(f"Checking: {name}")
    print(f"{'='*60}")
    
    if not Path(filepath).exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    found_issues = []
    found_allowed = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if '=' in line:
            key = line.split('=')[0].strip()
            
            # Check for forbidden JWT variables
            if key in FORBIDDEN_JWT_VARS:
                found_issues.append(f"Line {i}: ❌ FORBIDDEN: {key}")
            
            # Track allowed JWT variables
            if key in ALLOWED_JWT_VARS:
                found_allowed.append(f"Line {i}: ✅ ALLOWED: {key}")
    
    # Print results
    if found_allowed:
        print("\n✅ Allowed JWT Variables:")
        for item in found_allowed:
            print(f"  {item}")
    
    if found_issues:
        print("\n❌ FORBIDDEN Variables Found (DELETE THESE):")
        for item in found_issues:
            print(f"  {item}")
        return False
    else:
        print("\n✅ No forbidden JWT variables found!")
        return True

def main():
    backend_clean = check_env_file('.env', 'Backend .env')
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if backend_clean:
        print("✅ Backend .env is CLEAN!")
        print("\nYour .env should have ONLY these 3 JWT variables:")
        for var in sorted(ALLOWED_JWT_VARS):
            print(f"  ✓ {var}")
    else:
        print("❌ Backend .env has FORBIDDEN variables!")
        print("\nDELETE these lines from your .env:")
        for var in sorted(FORBIDDEN_JWT_VARS):
            print(f"  ✗ {var}")
    
    print("\n" + "="*60)
    print("IMPORTANT REMINDERS:")
    print("="*60)
    print("1. Frontend .env should NEVER have SECRET_KEY")
    print("2. Only backend needs JWT configuration")
    print("3. Match Render environment exactly")

if __name__ == '__main__':
    main()
