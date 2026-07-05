from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def hash_snapshot(payload: Any) -> str:
    return hashlib.sha256(stable_json_dumps(payload).encode("utf-8")).hexdigest()


def mask_ip(ip_address: str | None) -> str:
    if not ip_address:
        return "0.xxx.xxx.0"
    if ":" in ip_address:
        prefix = ip_address.split(":")[:2]
        return ":".join(prefix + ["xxxx", "xxxx", "xxxx", "xxxx"])[:39]
    parts = ip_address.split(".")
    if len(parts) != 4:
        return "0.xxx.xxx.0"
    return f"{parts[0]}.xxx.xxx.{parts[-1]}"
