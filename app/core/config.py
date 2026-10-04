from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RepForge"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./repforge.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

    @property
    def sqlalchemy_database_url(self) -> str:
        # Render and some providers provide postgres:// which SQLAlchemy 1.4+ expects as postgresql://
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()
