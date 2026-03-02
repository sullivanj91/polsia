from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    environment: str = "development"
    api_key: str = "dev-key"
    sandbox_mode: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://polsia:polsia_password@localhost:5432/polsia"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ChromaDB
    chroma_persist_dir: str = "/app/data/chroma"

    # Claude CLI
    claude_cli_path: str = "claude"
    claude_cli_mock: str = ""
    claude_cli_mock_response: str = '{"result": "Mock Claude response for testing"}'

    # External APIs
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_secret: str = ""
    twitter_bearer_token: str = ""

    google_ads_developer_token: str = ""
    google_ads_client_id: str = ""
    google_ads_client_secret: str = ""
    google_ads_refresh_token: str = ""
    google_ads_customer_id: str = ""

    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_access_token: str = ""
    meta_ad_account_id: str = ""

    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "agent@yourcompany.com"
    imap_host: str = "imap.gmail.com"
    imap_user: str = ""
    imap_password: str = ""

    hunter_io_api_key: str = ""
    tavily_api_key: str = ""

    github_token: str = ""
    vercel_token: str = ""
    railway_api_key: str = ""

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Scheduler
    morning_cycle_hour: int = 6
    evening_cycle_hour: int = 20


settings = Settings()
