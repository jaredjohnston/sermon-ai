#!/usr/bin/env python3
"""
Quick check of what the running server sees for CALLBACK_URL
"""
import os
from app.config.settings import settings

print("🔍 Environment Variable Check")
print("=" * 40)
print(f"os.getenv('CALLBACK_URL'): {os.getenv('CALLBACK_URL')}")
print(f"settings.CALLBACK_URL: {settings.CALLBACK_URL}")
print()

# Also check if .env file is being loaded
print("📋 Environment variables containing 'CALLBACK':")
for key, value in os.environ.items():
    if 'CALLBACK' in key:
        print(f"  {key} = {value}")
        
print()
print("🔧 Expected URL: https://charmed-stud-modest.ngrok-free.app/api/v1/transcription/callback")