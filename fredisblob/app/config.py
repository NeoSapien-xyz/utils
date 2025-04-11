from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    FIREBASE_CREDENTIALS: Path = Path("/secrets/firebase.json")
    GCP_CREDENTIALS_OLD: Path = Path("/secrets/gcp_secondbrain.json")
    GCP_CREDENTIALS_NEW: Path = Path("/secrets/gcp_avian.json")
    GCP_BUCKET_NAME_OLD: str = "neosapien_stagging"
    GCP_BUCKET_NAME_NEW: str = "neo-prod-yh3j5sd"
    GCP_CUTOFF_TIMESTAMP_MS: int = 1712611200000
    ENV: str = "prod"

    class Config:
        env_file = ".env"

settings = Settings()
