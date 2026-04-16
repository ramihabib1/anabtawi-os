import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_DB_URL = os.environ["SUPABASE_DB_URL"]

# Anthropic
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# OpenAI (Mem0 embeddings)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
RAMI_TELEGRAM_ID = os.environ.get("RAMI_TELEGRAM_ID", "")
FATHER_TELEGRAM_ID = os.environ.get("FATHER_TELEGRAM_ID", "")
MAREE_TELEGRAM_ID = os.environ.get("MAREE_TELEGRAM_ID", "")

# Advertising API (separate auth from SP-API)
ADS_API_CLIENT_ID = os.environ.get("ADS_API_CLIENT_ID", "")
ADS_API_CLIENT_SECRET = os.environ.get("ADS_API_CLIENT_SECRET", "")
ADS_API_REFRESH_TOKEN = os.environ.get("ADS_API_REFRESH_TOKEN", "")
ADS_API_PROFILE_ID = os.environ.get("ADS_API_PROFILE_ID", "")

# System
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# SP-API
SP_API_REFRESH_TOKEN = os.environ.get("SP_API_REFRESH_TOKEN", "")
SP_API_CLIENT_ID = os.environ.get("SP_API_CLIENT_ID", "")
SP_API_CLIENT_SECRET = os.environ.get("SP_API_CLIENT_SECRET", "")
SP_API_AWS_ACCESS_KEY = os.environ.get("SP_API_AWS_ACCESS_KEY", "")
SP_API_AWS_SECRET_KEY = os.environ.get("SP_API_AWS_SECRET_KEY", "")
SP_API_ROLE_ARN = os.environ.get("SP_API_ROLE_ARN", "")
SP_API_MARKETPLACE_CA = os.environ.get("SP_API_MARKETPLACE_CA", "A2EUQ1WTGCTBG2")
SP_API_MARKETPLACE_US = os.environ.get("SP_API_MARKETPLACE_US", "ATVPDKIKX0DER")

# Models
MODEL_DAILY = "claude-sonnet-4-20250514"
MODEL_CONSOLIDATION = "claude-opus-4-20250514"

# Business rules (L1 — immutable)
L1_RULES = """
L1 BUSINESS RULES (immutable — these override any other reasoning):
- NEVER recommend or execute financial actions without approval
- Minimum FBA days-of-supply alert threshold: 14 days
- Critical FBA days-of-supply threshold: 7 days
- Minimum FBA margin threshold: 15% (do not recommend prices below this)
- FBA inbound lead time: 5-7 business days (standard)
- Landed cost currency: CAD for CA marketplace, USD for US marketplace
- Seasonal products: Baklava (Ramadan +3x, Q4 holiday +1.5x)
- Reorder quantities must be in multiples of case pack size
- All PPC recommendations require approval regardless of amount
- Price changes require approval regardless of direction
""".strip()
