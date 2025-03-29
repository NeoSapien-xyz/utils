def format_transcript_from_json(data):
    if isinstance(data, dict) and "memory" in data:
        data = data["memory"]
    elif isinstance(data, list):
        pass
    else:
        raise ValueError("Input file must be a 'memory' JSON or a transcript array.")

    lines = []
    for item in data:
        speaker = item.get("speaker", "Unknown")
        text = item.get("text", "")
        lines.append(f"{speaker}: {text}")
    return "\n\n".join(lines)

