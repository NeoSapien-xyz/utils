from collections import defaultdict
from datetime import datetime

def extract_trend_data_by_user(chunk_loss_result, include_tooltip=False):
    user_trends = {}

    for user in chunk_loss_result["users"]:
        bucket = defaultdict(list)
        tooltip_bucket = defaultdict(list)
        all_days = set()

        for mem in user["memories"]:
            ts = mem.get("started_at_str")
            loss_pct = mem.get("loss_pct")
            tooltip = mem.get("tooltip") if include_tooltip else None
            if ts:
                day = ts.split(" ")[0]
                all_days.add(day)

                if isinstance(loss_pct, (int, float)):
                    capped_loss_pct = loss_pct if loss_pct >= -100 else -101
                    bucket[day].append(capped_loss_pct)
                    if include_tooltip:
                        if loss_pct < -100:
                            fs = mem.get("fs_duration", "?")
                            gs = mem.get("audio_duration", "?")
                            tooltip = f"GCP overrun → FS {fs}s / GCP {gs}s"
                        tooltip_bucket[day].append(tooltip or f"{loss_pct}%")

        trend_data = []
        for day in sorted(all_days):
            vals = bucket.get(day, [])
            tooltips = tooltip_bucket.get(day, []) if include_tooltip else None
            avg = round(sum(vals) / len(vals), 2) if vals else 0.0
            tooltip_str = tooltips[0] if tooltips else f"{avg}%"
            trend_data.append({"date": day, "avg_loss_pct": avg, "tooltip": tooltip_str})

        user_trends[user["user_id"]] = trend_data

    return user_trends


def build_daily_user_memory_map(chunk_loss_result):
    daily = defaultdict(lambda: defaultdict(lambda: {"memories": [], "summary": {}}))

    for user in chunk_loss_result["users"]:
        uid = user["user_id"]
        for mem in user["memories"]:
            date = mem.get("started_at_str", "?").split(" ")[0]
            fs = mem.get("fs_duration")
            gs = mem.get("audio_duration")
            loss = mem.get("loss")
            loss_pct = mem.get("loss_pct")
            memory_id = mem.get("memory_id")

            daily[date][uid]["memories"].append({
                "memory_id": memory_id,
                "fs_duration": fs,
                "gcp_duration": gs,
                "loss": loss,
                "loss_pct": loss_pct
            })

    for date in daily:
        for uid in daily[date]:
            mems = daily[date][uid]["memories"]
            total_fs = sum(m.get("fs_duration", 0) or 0 for m in mems if isinstance(m.get("fs_duration"), (int, float)))
            total_gcp = sum(m.get("gcp_duration", 0) or m.get("audio_duration", 0) or 0 for m in mems if isinstance(m.get("audio_duration"), (int, float)))
            total_loss = sum(m.get("loss", 0) or 0 for m in mems if isinstance(m.get("loss"), (int, float)))
            valid = [m for m in mems if isinstance(m.get("loss_pct"), (int, float))]
            avg_pct = round(sum(m["loss_pct"] for m in valid) / len(valid), 2) if valid else 0.0

            daily[date][uid]["summary"] = {
                "count": len(mems),
                "total_fs_duration": round(total_fs, 2),
                "total_gcp_duration": round(total_gcp, 2),
                "total_loss": round(total_loss, 2),
                "avg_loss_pct": avg_pct
            }

    return daily

