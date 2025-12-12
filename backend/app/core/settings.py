"""
FilaOps ERP - Configuration Management with pydantic-settings

Provides validated, type-safe configuration from environment variables.
All settings can be overridden via environment variables or .env file.
"""
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    Environment variables take precedence over .env file values.
    Prefix BLB3D_ can be used for any setting (e.g., BLB3D_DEBUG=true).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # ===================
    # Application Settings
    # ===================
    PROJECT_NAME: str = "FilaOps"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="deployment environment")

    # ===================
    # Database Settings
    # ===================
    DB_HOST: str = Field(default="localhost\\SQLEXPRESS", description="SQL Server host")
    DB_NAME: str = Field(default="BLB3D_ERP", description="Database name")
    DB_USER: Optional[str] = Field(default=None, description="Database user (if not using trusted connection)")
    DB_PASSWORD: Optional[str] = Field(default=None, description="Database password")
    DB_TRUSTED_CONNECTION: bool = Field(default=True, description="Use Windows authentication")
    DATABASE_URL: Optional[str] = Field(default=None, description="Full database URL (overrides other DB_ settings)")

    @property
    def database_url(self) -> str:
        """Build database URL from components or use explicit URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.DB_TRUSTED_CONNECTION:
            return f"mssql+pyodbc://{self.DB_HOST}/{self.DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
        else:
            return f"mssql+pyodbc://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"

    # ===================
    # Security Settings
    # ===================
    SECRET_KEY: str = Field(
        default="change-this-to-a-random-secret-key-in-production",
        description="JWT signing key - MUST change in production"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT token expiration in minutes")
    API_KEY: Optional[str] = Field(default=None, description="API key for external integrations")

    @field_validator("SECRET_KEY")
    @classmethod
    def warn_default_secret(cls, v: str) -> str:
        """Warn if using default secret key."""
        if "change-this" in v.lower():
            import warnings
            warnings.warn(
                "Using default SECRET_KEY - this is insecure for production!",
                UserWarning
            )
        return v

    # ===================
    # CORS Settings
    # ===================
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ===================
    # Bambu Print Suite Integration
    # ===================
    BAMBU_SUITE_API_URL: str = Field(
        default="http://localhost:8001",
        description="Bambu Print Suite API URL"
    )
    BAMBU_SUITE_API_KEY: Optional[str] = Field(default=None, description="API key for Bambu Suite")

    # ===================
    # File Storage Settings
    # ===================
    UPLOAD_DIR: str = Field(default="./uploads/quotes", description="Directory for uploaded files")
    MAX_FILE_SIZE_MB: int = Field(default=100, description="Maximum upload file size in MB")
    ALLOWED_FILE_FORMATS: List[str] = Field(
        default=[".3mf", ".stl"],
        description="Allowed file upload extensions"
    )

    @field_validator("ALLOWED_FILE_FORMATS", mode="before")
    @classmethod
    def parse_file_formats(cls, v):
        """Parse comma-separated string to list."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",") if fmt.strip()]
        return v

    # ===================
    # Google Cloud Storage
    # ===================
    GCS_ENABLED: bool = Field(default=False, description="Enable GCS backup")
    GCS_BUCKET_NAME: str = Field(default="blb3d-quote-files", description="GCS bucket name")
    GCS_PROJECT_ID: Optional[str] = Field(default=None, description="GCP project ID")
    GCS_CREDENTIALS_PATH: Optional[str] = Field(default=None, description="Path to GCS service account JSON")

    # ===================
    # Google Drive Integration
    # ===================
    GDRIVE_ENABLED: bool = Field(default=False, description="Enable Google Drive integration")
    GDRIVE_CREDENTIALS_PATH: Optional[str] = Field(default=None, description="Path to Drive credentials")
    GDRIVE_FOLDER_ID: Optional[str] = Field(default=None, description="Drive folder ID for uploads")

    # ===================
    # Stripe Payment Integration
    # ===================
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, description="Stripe secret API key")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, description="Stripe publishable key")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="Stripe webhook signing secret")

    # ===================
    # EasyPost Shipping Integration
    # ===================
    EASYPOST_API_KEY: Optional[str] = Field(default=None, description="EasyPost API key")
    EASYPOST_TEST_MODE: bool = Field(default=True, description="Use EasyPost test mode")

    # ===================
    # Email Configuration (SMTP)
    # ===================
    SMTP_HOST: str = Field(default="smtp.gmail.com", description="SMTP server host")
    SMTP_PORT: int = Field(default=587, description="SMTP server port")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_FROM_EMAIL: str = Field(default="noreply@example.com", description="From email address")
    SMTP_FROM_NAME: str = Field(default="Your Company Name", description="From display name")
    SMTP_TLS: bool = Field(default=True, description="Use TLS for SMTP")

    # ===================
    # Admin Settings
    # ===================
    ADMIN_APPROVAL_EMAIL: str = Field(
        default="admin@example.com",
        description="Admin email for approvals"
    )

    # ===================
    # Ship From Address (Business Address)
    # ===================
    # NOTE: These default values should be configured via environment variables
    # for production deployments. Replace with your actual business address.
    SHIP_FROM_NAME: str = Field(default="Your Company Name")
    SHIP_FROM_STREET1: str = Field(default="123 Main Street")
    SHIP_FROM_STREET2: Optional[str] = Field(default=None)
    SHIP_FROM_CITY: str = Field(default="Your City")
    SHIP_FROM_STATE: str = Field(default="ST")
    SHIP_FROM_ZIP: str = Field(default="12345")
    SHIP_FROM_COUNTRY: str = Field(default="US")
    SHIP_FROM_PHONE: str = Field(default="555-555-5555")

    # ===================
    # Frontend Settings
    # ===================
    FRONTEND_URL: str = Field(default="http://localhost:5173", description="Frontend URL for redirects")

    # ===================
    # Redis / Background Jobs
    # ===================
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for Celery")

    # ===================
    # Logging Settings
    # ===================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path (optional)")
    AUDIT_LOG_FILE: Optional[str] = Field(default="./logs/audit.log", description="Audit log file path")

    # ===================
    # WooCommerce Integration (future)
    # ===================
    WOOCOMMERCE_URL: Optional[str] = Field(default=None, description="WooCommerce store URL")
    WOOCOMMERCE_KEY: Optional[str] = Field(default=None, description="WooCommerce consumer key")
    WOOCOMMERCE_SECRET: Optional[str] = Field(default=None, description="WooCommerce consumer secret")
    WOOCOMMERCE_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="WooCommerce webhook secret")

    # ===================
    # QuickBooks Integration (future)
    # ===================
    QUICKBOOKS_CLIENT_ID: Optional[str] = Field(default=None)
    QUICKBOOKS_CLIENT_SECRET: Optional[str] = Field(default=None)
    QUICKBOOKS_REDIRECT_URI: Optional[str] = Field(default=None)
    QUICKBOOKS_ENVIRONMENT: str = Field(default="sandbox")

    # ===================
    # Product Tier Settings
    # ===================
    TIER: str = Field(
        default="open",
        description="Product tier: open, pro, or enterprise"
    )
    LICENSE_KEY: Optional[str] = Field(
        default=None,
        description="License key for Pro/Enterprise features"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_pro_tier(self) -> bool:
        """Check if Pro tier or higher"""
        return self.TIER.lower() in ("pro", "enterprise")

    @property
    def is_enterprise_tier(self) -> bool:
        """Check if Enterprise tier"""
        return self.TIER.lower() == "enterprise"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are only loaded once per process,
    improving performance and ensuring consistency.
    """
    return Settings()


# Convenience alias for backward compatibility with existing code
settings = get_settings()
