from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str = Field(..., env='POSTGRES_USER')
    POSTGRES_PASSWORD: str = Field(..., env='POSTGRES_PASSWORD')
    POSTGRES_SERVER: str = Field(..., env='POSTGRES_SERVER')
    POSTGRES_PORT: str = Field(..., env='POSTGRES_PORT')
    POSTGRES_DB: str = Field(..., env='POSTGRES_DB')

    class Config:
        env_file = '.env'
        case_sensitive = True

settings = Settings()