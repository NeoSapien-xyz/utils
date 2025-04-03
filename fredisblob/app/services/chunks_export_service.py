
import io, csv
from datetime import datetime
from app.core.firebase import init_firebase
from app.core.gcs import init_gcs

GCS_BUCKET = "neosapien_stagging"
BYTES_PER_SECOND = 32000

def format_ts(ts):
    if not ts:
        return ""
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_all_user_ids():
    db = init_firebase()
    return [doc.id for doc in db.collection("users").stream()]

def generate_chunks_csv(user_ids):
    db = init_firebase()
    gcs_client = init_gcs()
    bucket = gcs_client.bucket(GCS_BUCKET)
    rows = []

    for uid in user_ids:
        # Firestore
        fs_mems = db.collection("users").document(uid).collection("memories").stream()
        mem_map = {}
        for doc in fs_mems:
            data = doc.to_dict()
            start, end = data.get("started_at"), data.get("finished_at")
            fs_duration = None
            if start and end:
                start_ts = start.timestamp()
                end_ts = end.timestamp()
                fs_duration = round(end_ts - start_ts, 2)
            mem_map[doc.id] = {
                "fs_duration": fs_duration,
                "fs_started_at": format_ts(start),
                "fs_finished_at": format_ts(end)
            }

        # GCS
        prefix = f"{uid}/memory_data/"
        gcs_blobs = list(bucket.list_blobs(prefix=prefix))
        gcs_memories = {}

        for blob in gcs_blobs:
            parts = blob.name.split("/")
            if len(parts) < 4:
                continue
            mem_id = parts[2]
            if mem_id not in gcs_memories:
                gcs_memories[mem_id] = {"total_size": 0, "times": []}
            gcs_memories[mem_id]["total_size"] += blob.size
            gcs_memories[mem_id]["times"].append(blob.time_created)

        # Merge
        all_mem_ids = set(mem_map.keys()) | set(gcs_memories.keys())
        for mem_id in all_mem_ids:
            fs = mem_map.get(mem_id, {})
            gcs = gcs_memories.get(mem_id, {})
            row = [
                uid,
                mem_id,
                fs.get("fs_duration", ""),
                round(gcs["total_size"] / BYTES_PER_SECOND, 2) if gcs else "",
                format_ts(min(gcs["times"])) if gcs and gcs["times"] else "",
                fs.get("fs_started_at", ""),
                fs.get("fs_finished_at", "")
            ]
            rows.append(row)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user_id", "memory_id", "fs_duration", "gcp_audio_duration", "gcp_started_at", "fs_started_at", "fs_finished_at"])
    writer.writerows(rows)
    output.seek(0)
    return output
