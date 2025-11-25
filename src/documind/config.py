"""
DocuMind Configuration

Environment variables and application settings.
"""

import os
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


# API Keys
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY")

# Database (Session 4+)
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_ANON_KEY = get_env("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = get_env("SUPABASE_SERVICE_KEY")

# Application Settings
DEBUG = get_env("DEBUG", "false").lower() == "true"
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")


def validate_config() -> bool:
    """Validate that required configuration is present."""
    required = ["ANTHROPIC_API_KEY"]
    missing = [key for key in required if not get_env(key)]

    if missing:
        print(f"Missing required environment variables: {missing}")
        return False
    return True
