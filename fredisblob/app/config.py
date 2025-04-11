from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    FIREBASE_CREDENTIALS: Path = Path("/secrets/firebase.json")
    GCP_CREDENTIALS: Path = Path("/secrets/gcp.json")
    GCP_BUCKET_NAME: str = "neosapien_stagging"
    ENV: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()
