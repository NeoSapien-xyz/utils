from app.core.firebase import init_firebase
from google.cloud.firestore import Client
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds

db: Client = init_firebase()

def _convert_datetime_fields(data):
    """Convert DatetimeWithNanoseconds fields to timestamps."""
    if not data:
        return data
    
    result = {}
    for key, value in data.items():
        if isinstance(value, DatetimeWithNanoseconds):
            result[key] = int(value.timestamp() * 1000)  # Convert to milliseconds
        elif isinstance(value, dict):
            result[key] = _convert_datetime_fields(value)
        elif isinstance(value, list):
            result[key] = [_convert_datetime_fields(item) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    return result

async def fetch_user_memories(user_id: str, memory_id=None, started_at=None, finished_at=None, page=1, page_size=10):
    col_ref = db.collection("users").document(user_id).collection("memories")

    if memory_id:
        doc = col_ref.document(memory_id).get()
        if doc.exists:
            return {"memories": [_convert_datetime_fields(doc.to_dict())], "total": 1}
        return {"memories": [], "total": 0}

    query = col_ref

    if started_at:
        query = query.where("started_at", ">=", started_at)
    if finished_at:
        query = query.where("started_at", "<=", finished_at)

    # Firestore doesn't support compound ordering with where unless indexed,
    # so we fetch then sort manually
    docs = query.stream()
    all_docs = [doc.to_dict() for doc in docs]

    # Sort by created_at DESC
    all_docs_sorted = sorted(all_docs, key=lambda d: d.get("created_at", 0), reverse=True)

    total = len(all_docs_sorted)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = all_docs_sorted[start_idx:end_idx]

    return {
        "memories": [_convert_datetime_fields(doc) for doc in paginated],
        "total": total,
        "page": page,
        "page_size": page_size
    }

async def get_memory_json(user_id: str, memory_id: str):
    doc_ref = db.collection("users").document(user_id).collection("memories").document(memory_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise Exception(f"Memory {memory_id} not found.")
    return _convert_datetime_fields(doc.to_dict())

