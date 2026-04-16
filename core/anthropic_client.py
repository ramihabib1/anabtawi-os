from anthropic import Anthropic
from core.config import ANTHROPIC_API_KEY

_client: Anthropic | None = None


def get_anthropic() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client
