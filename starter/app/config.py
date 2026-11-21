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
    # Separate WhatsApp line for operator onboarding (kept distinct from the call number).
    kaayal_whatsapp_number: str | None = None
    # wa-bot send listener (compose internal only). Unset = no push on approval.
    wa_bot_url: str | None = None
    # Callback engine: "simulator" (no real calls) or "sarvam" (real dialing —
    # owner-approved 2026-11-22; per-call charges apply).
    outbound_provider: str = "simulator"
    # Sarvam Instant Outbound — real calls. All required when provider=sarvam.
    sarvam_api_key: str | None = None
    sarvam_org_id: str | None = None
    sarvam_workspace_id: str | None = None
    sarvam_outbound_app_id: str | None = None
    sarvam_outbound_app_version: int | None = None
    sarvam_connection_id: str | None = None
    sarvam_agent_phone_number: str | None = None
    # How long place() polls the analytics API for the attempt outcome.
    sarvam_outbound_timeout_seconds: int = 300
    # Simulated customer answer: interested | not_interested | no_answer.
    sim_callback_outcome: str = "interested"
    callback_tick_seconds: int = 30
    # Demo escape hatch: bypass the 09:00–18:00 IST calling window. Default off.
    demo_ignore_call_window: bool = False


def get_settings() -> Settings:
    return Settings()
