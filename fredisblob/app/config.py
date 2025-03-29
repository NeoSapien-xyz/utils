from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    FIREBASE_CREDENTIALS: Path = Path("/secrets/firebase.json")
    GCP_CREDENTIALS: Path = Path("/secrets/gcp.json")
    ENV: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
