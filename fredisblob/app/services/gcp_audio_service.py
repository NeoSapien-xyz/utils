import os
import wave
import tempfile
import numpy as np
from google.cloud import storage
from pathlib import Path
from app.config import settings
from app.core.firebase import init_firebase
from google.oauth2 import service_account


def download_and_merge_chunks(user_id: str, memory_id: str, vad: bool = False, frame_rate=16000, byte_order='little') -> str:
    folder = "novad_chunks" if not vad else "audio_chunks"
    prefix = f"{user_id}/memory_data/{memory_id}/{folder}/"

    storage_client, bucket_name = right_storage_client_and_bucket(user_id, memory_id)
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    print(f"path is {bucket_name}://{prefix}")
    if not blobs:
        raise Exception(f"No audio chunks found in {prefix}")

    # Sort blobs by filename (epoch timestamp assumed)
    blobs = sorted(blobs, key=lambda b: b.name)

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_dir = os.path.join(temp_dir, "intermediate_wavs")
        Path(wav_dir).mkdir(parents=True, exist_ok=True)

        wav_files = []

        for blob in blobs:
            raw_data = blob.download_as_bytes()
            if not raw_data:
                continue

            # Convert raw to wav file
            pcm_path = os.path.join(temp_dir, os.path.basename(blob.name))
            with open(pcm_path, "wb") as f:
                f.write(raw_data)

            wav_path = os.path.join(wav_dir, f"{os.path.splitext(os.path.basename(blob.name))[0]}.wav")
            converted = pcm_to_wav(pcm_path, wav_path, channels=1, frame_rate=frame_rate, sample_width=2, byte_order=byte_order)
            if converted:
                wav_files.append(converted)

        if not wav_files:
            raise Exception("No valid chunks converted to WAV")

        final_output = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        combine_wav_files(wav_files, final_output)
        return final_output


def pcm_to_wav(pcm_file_path, wav_file_path, channels=1, frame_rate=16000, sample_width=2, byte_order='little'):
    if not os.path.exists(pcm_file_path) or os.path.getsize(pcm_file_path) == 0:
        return None

    with open(pcm_file_path, 'rb') as pcm_file:
        pcm_data = pcm_file.read()

    if sample_width == 1:
        dtype = np.uint8
    elif sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32

    audio_array = np.frombuffer(pcm_data, dtype=dtype)

    if byte_order == 'big':
        audio_array = audio_array.byteswap()

    with wave.open(wav_file_path, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setframerate(frame_rate)
        wav_file.setsampwidth(sample_width)
        wav_file.writeframes(audio_array.tobytes())

    return wav_file_path


def combine_wav_files(wav_files, output_path):
    if not wav_files:
        return

    with wave.open(wav_files[0], 'rb') as first:
        params = first.getparams()

    with wave.open(output_path, 'wb') as out:
        out.setparams(params)
        for wf in wav_files:
            with wave.open(wf, 'rb') as w:
                out.writeframes(w.readframes(w.getnframes()))


def get_gcs_client_for_created_at(created_at_ms: int) -> storage.Client:
    """
    Return GCS client based on created_at timestamp.
    """
    print(f"{created_at_ms=}, {settings.GCP_CUTOFF_TIMESTAMP_MS=}")
    if created_at_ms > settings.GCP_CUTOFF_TIMESTAMP_MS:
        print("old memory, fetching old creds")
        creds_path = settings.GCP_CREDENTIALS_OLD
        bucket_name = settings.GCP_BUCKET_NAME_OLD
    else:
        print("new memory, fetching new creds")
        creds_path = settings.GCP_CREDENTIALS_NEW
        bucket_name = settings.GCP_BUCKET_NAME_NEW

    credentials = service_account.Credentials.from_service_account_file(str(creds_path))
    return storage.Client(credentials=credentials, project=credentials.project_id), bucket_name

def right_storage_client_and_bucket(user_id, memory_id):
    db: Client = init_firebase()
    doc = db.collection("users").document(user_id).collection("memories").document(memory_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Memory not found")
    created_at = int(doc.to_dict().get("created_at", 0).timestamp() * 1000)
    print(f"created at is {created_at}")
    return get_gcs_client_for_created_at(created_at)
    
