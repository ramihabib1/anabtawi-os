"""
Settings adapter for the sync layer.

Wraps core/config.py constants into a settings object with attribute access,
matching the pattern used in all ported SP-API clients and jobs.
"""

from __future__ import annotations

from types import SimpleNamespace

import core.config as _c

settings = SimpleNamespace(
    # Supabase
    SUPABASE_URL=_c.SUPABASE_URL,
    SUPABASE_SERVICE_KEY=_c.SUPABASE_SERVICE_KEY,

    # SP-API
    SP_API_REFRESH_TOKEN=_c.SP_API_REFRESH_TOKEN,
    SP_API_CLIENT_ID=_c.SP_API_CLIENT_ID,
    SP_API_CLIENT_SECRET=_c.SP_API_CLIENT_SECRET,
    SP_API_AWS_ACCESS_KEY=_c.SP_API_AWS_ACCESS_KEY,
    SP_API_AWS_SECRET_KEY=_c.SP_API_AWS_SECRET_KEY,
    SP_API_ROLE_ARN=_c.SP_API_ROLE_ARN,
    SP_API_MARKETPLACE_CA=_c.SP_API_MARKETPLACE_CA,
    SP_API_MARKETPLACE_US=_c.SP_API_MARKETPLACE_US,
    SP_API_BASE_URL="https://sellingpartnerapi-na.amazon.com",

    # LWA token endpoint
    LWA_TOKEN_URL="https://api.amazon.com/auth/o2/token",

    # Advertising API
    ADS_API_CLIENT_ID=_c.ADS_API_CLIENT_ID,
    ADS_API_CLIENT_SECRET=_c.ADS_API_CLIENT_SECRET,
    ADS_API_REFRESH_TOKEN=_c.ADS_API_REFRESH_TOKEN,
    ADS_API_PROFILE_ID=_c.ADS_API_PROFILE_ID,
    ADS_API_BASE_URL="https://advertising-api.amazon.com",

    # Telegram
    TELEGRAM_BOT_TOKEN=_c.TELEGRAM_BOT_TOKEN,
    RAMI_TELEGRAM_ID=_c.RAMI_TELEGRAM_ID,
    FATHER_TELEGRAM_ID=_c.FATHER_TELEGRAM_ID,
    MAREE_TELEGRAM_ID=_c.MAREE_TELEGRAM_ID,

    # System
    LOG_LEVEL=_c.LOG_LEVEL,
    ENVIRONMENT=_c.ENVIRONMENT,

    # Known active ASIN used as probe for seller ID discovery (Almond Fingers 375g)
    PROBE_ASIN="B0FT3HN2XV",
)

# Computed flag — mirrors pydantic-settings is_production property from habib-os
settings.is_production = settings.ENVIRONMENT == "production"
