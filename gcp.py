# gcp.py

from google.cloud import storage

BUCKET_NAME = "neosapien_stagging"
CHUNK_EXTENSION = ".raw"
BITRATE_KBPS = 256
BITS_PER_BYTE = 8

def analyze_user_chunks(user_id):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    prefix = f"{user_id}/memory_data/"
    blobs = list(client.list_blobs(BUCKET_NAME, prefix=prefix))

    # Group blobs by memory_id
    memory_map = {}
    for blob in blobs:
        parts = blob.name.split("/")
        if len(parts) < 5:
            continue
        memory_id = parts[2]
        if parts[3] != "novad_chunks":
            continue
        memory_map.setdefault(memory_id, {"chunks": [], "created_at": blob.time_created})
        memory_map[memory_id]["chunks"].append(blob)

    # Sort memory_ids by created_at desc
    sorted_memories = sorted(memory_map.items(), key=lambda x: x[1]["created_at"], reverse=True)

    results = []
    for memory_id, info in sorted_memories:
        chunks = info["chunks"]
        total_size = sum(blob.size for blob in chunks)
        avg_chunk_size = total_size / len(chunks) if chunks else 0
        estimated_duration = (total_size * BITS_PER_BYTE) / (BITRATE_KBPS * 1000)

        results.append({
            "memory_id": memory_id,
            "created_at": info["created_at"].isoformat(),
            "chunk_count": len(chunks),
            "total_size_kb": total_size / 1024,
            "avg_chunk_size_kb": avg_chunk_size / 1024,
            "estimated_duration_sec": estimated_duration
        })

    return results

