from app.core.firebase import init_firebase
from google.cloud import firestore
from google.cloud.firestore import Client
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from typing import Optional
from datetime import datetime

db: Client = init_firebase()

def _convert_datetime_fields(data):
    """Convert DatetimeWithNanoseconds fields to timestamps."""
    if not data:
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, DatetimeWithNanoseconds):
            result[key] = int(value.timestamp() * 1000)  # ms
        elif isinstance(value, dict):
            result[key] = _convert_datetime_fields(value)
        elif isinstance(value, list):
            result[key] = [
                _convert_datetime_fields(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            result[key] = value
    return result


async def fetch_user_memories(
    user_id: str,
    memory_id: Optional[str] = None,
    started_at: Optional[int] = None,
    finished_at: Optional[int] = None,
    page: int = 1,
    page_size: int = 10,
    **kwargs  # ignoring cursor/direction
):
    print(f"[DEBUG] for user_id={user_id} memory_id={memory_id} started_at={started_at} finished_at={finished_at} page={page} page_size={page_size}")
    col_ref = db.collection("users").document(user_id).collection("memories")

    if memory_id:
        doc = col_ref.document(memory_id).get()
        if doc.exists:
            return {"memories": [_convert_datetime_fields(doc.to_dict())], "total": 1}
        return {"memories": [], "total": 0}

    query = col_ref.order_by("created_at", direction=firestore.Query.DESCENDING)

    if started_at:
        query = query.where("started_at", ">=", started_at)
    if finished_at:
        query = query.where("started_at", "<=", finished_at)

    all_docs = list(query.stream())
    total = len(all_docs)

    skip_count = (page - 1) * page_size
    paginated_docs = all_docs[skip_count: skip_count + page_size]

    print(f"[DEBUG] Total docs: {total}, returning {len(paginated_docs)} from offset {skip_count}")

    results = [
        {**_convert_datetime_fields(doc.to_dict()), "memory_id": doc.id}
        for doc in paginated_docs
    ]

    return {
        "memories": results,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": skip_count + page_size < total,
        "has_prev": page > 1
    }


async def get_memory_json(user_id: str, memory_id: str):
    doc_ref = db.collection("users").document(user_id).collection("memories").document(memory_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise Exception(f"Memory {memory_id} not found.")
    return _convert_datetime_fields(doc.to_dict())
