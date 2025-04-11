from google.cloud import storage
from app.config import settings
import os

_gcs_client = None

def init_gcs():
    global _gcs_client
    if _gcs_client is None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(settings.GCP_CREDENTIALS_NEW)
        _gcs_client = storage.Client()
    return _gcs_client
