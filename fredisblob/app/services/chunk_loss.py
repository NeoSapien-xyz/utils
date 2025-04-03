from collections import defaultdict
from app.core.firebase import init_firebase
from app.core.gcs import init_gcs
from datetime import datetime

GCS_BUCKET = "neosapien_stagging"
BITRATE_BYTES_PER_SEC = 32000  # 256 kbps

def analyze_chunk_loss(user_ids):
    fs_client = init_firebase()
    gcs_client = init_gcs()
    bucket = gcs_client.bucket(GCS_BUCKET)

    result = []
    overall_loss = 0
    memory_count = 0
    missing_in_gcs = []
    missing_in_fs = []

    if not user_ids:
        user_ids = [user.id for user in fs_client.collection("users").list_documents()]

    for uid in user_ids:
        try:
            mems_ref = fs_client.collection("users").document(uid).collection("memories")
            mem_docs = mems_ref.stream()
            mem_ids_fs = {}
            user_total_loss = 0

            # First: process Firestore memories
            for doc in mem_docs:
                try:
                    mem_id = doc.id
                    data = doc.to_dict()
                    start = data.get("started_at")
                    end = data.get("finished_at")

                    if not start or not end:
                        continue

                    if hasattr(start, 'timestamp'):
                        start_ts = start.timestamp()
                        end_ts = end.timestamp()
                    else:
                        start_ts = int(start) / 1e9
                        end_ts = int(end) / 1e9

                    fs_duration = end_ts - start_ts
                    fs_started_at = datetime.fromtimestamp(start_ts)

                    mem_ids_fs[mem_id] = {
                        "memory_id": mem_id,
                        "fs_duration": round(fs_duration, 2),
                        "audio_duration": None,
                        "loss": None,
                        "loss_pct": None,
                        "started_at": start_ts,
                        "started_at_str": fs_started_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "has_fs": True,
                        "has_gcs": False
                    }
                except Exception:
                    continue

            # Second: process GCS memory chunks
            gcs_prefix = f"{uid}/memory_data/"
            gcs_blobs = gcs_client.list_blobs(GCS_BUCKET, prefix=gcs_prefix, delimiter="/")
            gcs_mem_ids = set()
            for page in gcs_blobs.pages:
                for prefix in page.prefixes:
                    parts = prefix.split("/")
                    if len(parts) >= 4:
                        mem_id = parts[2]
                        gcs_mem_ids.add(mem_id)

            for mem_id in gcs_mem_ids:
                prefix = f"{uid}/memory_data/{mem_id}/novad_chunks/"
                blobs = gcs_client.list_blobs(GCS_BUCKET, prefix=prefix)
                total_bytes = 0
                chunk_times = []

                for blob in blobs:
                    total_bytes += blob.size
                    chunk_times.append(blob.time_created)

                if not chunk_times:
                    continue

                first_time = min(chunk_times)
                gcs_started_at = first_time.timestamp()
                gcs_started_str = first_time.strftime("%Y-%m-%d %H:%M:%S")
                audio_duration = total_bytes / BITRATE_BYTES_PER_SEC

                if mem_id in mem_ids_fs:
                    entry = mem_ids_fs[mem_id]
                    chunk_loss = entry["fs_duration"] - audio_duration
                    loss_pct = (chunk_loss / entry["fs_duration"]) * 100 if entry["fs_duration"] > 0 else 0
                    entry.update({
                        "audio_duration": round(audio_duration, 2),
                        "loss": round(chunk_loss, 2),
                        "loss_pct": round(loss_pct, 2),
                        "has_gcs": True,
                        "started_at": gcs_started_at,
                        "started_at_str": gcs_started_str,
                        "tooltip": f"Loss: {round(chunk_loss, 2)}s of {round(entry['fs_duration'], 2)}s → {round(loss_pct, 2)}%"
                    })
                else:
                    missing_in_fs.append((uid, mem_id))
                    mem_ids_fs[mem_id] = {
                        "memory_id": mem_id,
                        "fs_duration": None,
                        "audio_duration": round(audio_duration, 2),
                        "loss": None,
                        "loss_pct": None,
                        "started_at": gcs_started_at,
                        "started_at_str": gcs_started_str,
                        "has_fs": False,
                        "has_gcs": True
                    }

            for mem_id in mem_ids_fs:
                if not mem_ids_fs[mem_id]["has_gcs"]:
                    missing_in_gcs.append((uid, mem_id))

            sorted_memories = sorted(mem_ids_fs.values(), key=lambda x: x.get("started_at", 0), reverse=True)
            total_loss = sum(entry["loss"] for entry in sorted_memories if isinstance(entry["loss"], (float, int)))
            valid_loss_entries = [m for m in sorted_memories if isinstance(m["loss"], (float, int))]
            avg_loss = total_loss / len(valid_loss_entries) if valid_loss_entries else 0

            print(f"sorted memories are {sorted_memories}")
            print(f"total loss {total_loss}")
            print(f"valid loss entries {valid_loss_entries}")
            print(f"{avg_loss=}")

            result.append({
                "user_id": uid,
                "memories": sorted_memories,
                "total_loss": round(total_loss, 2),
                "avg_loss": round(avg_loss, 2)
            })
            overall_loss += total_loss
            memory_count += len(valid_loss_entries)

        except Exception as user_err:
            result.append({
                "user_id": uid,
                "memories": [],
                "total_loss": 0,
                "avg_loss": 0,
                "error": str(user_err)
            })

    overall_avg = overall_loss / memory_count if memory_count else 0
    return {
        "users": result,
        "missing_in_gcs": missing_in_gcs,
        "missing_in_fs": missing_in_fs,
        "overall_avg": round(overall_avg, 2)
    }

