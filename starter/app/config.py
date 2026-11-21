from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    sarvam_tool_shared_secret: str | None = None
    kaayal_public_base_url: str = "https://your-tunnel.example"
    port: int = 8000
    openai_timeout_seconds: float = 12.0
    openai_max_output_tokens: int = 180
    log_level: str = "INFO"
    # Simple in-process guard so a misconfigured tool can't hammer OpenAI.
    rate_limit_per_minute: int = 60
    # Speakable replies should stay short; hard cap returned text.
    reply_max_chars: int = 600
    # Hard cap on raw request body regardless of JSON validation.
    max_body_bytes: int = 16_384
    # Phase 2: SQLite catalog store.
    database_url: str = "sqlite:///kaayal.db"
    # Owner admin token (?t= on /admin). Operators use unguessable URLs, no login.
    admin_token: str | None = None
    # Public call-in number shown on the landing page (E.164 or display format).
    kaayal_phone_number: str | None = None


def get_settings() -> Settings:
    return Settings()
