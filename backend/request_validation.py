"""Read bounded UTF-8 JSON before applying endpoint-specific schemas."""

import json

from fastapi import HTTPException, Request


def unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field.")
        result[key] = value
    return result


def reject_nonfinite(value: str):
    raise ValueError("Non-finite JSON numbers are not supported.")


async def read_json(request: Request, max_bytes: int):
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise HTTPException(415, "Send this request as JSON.")
    if request.headers.get("content-encoding", "identity").lower() != "identity":
        raise HTTPException(415, "Compressed request bodies are not supported.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > max_bytes:
            raise HTTPException(413, "The request is too large.")
        content.extend(chunk)
    try:
        return json.loads(content.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=reject_nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        raise HTTPException(422, "Send a valid JSON object with unique fields.") from None
