"""Shared helpers for the MCP tools in this package."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def ok(data: Any) -> dict[str, Any]:
    """Wrap a successful tool result."""
    return {"success": True, "data": data, "timestamp": now_iso()}


def err(message: str) -> dict[str, Any]:
    """Wrap a failed tool result."""
    return {"success": False, "error": message, "timestamp": now_iso()}


def human_bytes(num: float | int | None) -> str | None:
    """Format a byte count using binary units."""
    if num is None:
        return None
    value = float(num)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(value) < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} EB"


def run(cmd: list[str], timeout: float = 10.0) -> subprocess.CompletedProcess[str] | None:
    """Run a command without a shell, returning None if it is missing or times out."""
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def read_text(path: str) -> str | None:
    """Read a small text file, returning None when it is unavailable."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except OSError:
        return None


def to_float(value: Any) -> float | None:
    """Extract a float from values such as ``42``, ``42.5 %`` or ``N/A``."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if text.upper() in {"", "N/A", "NA", "[N/A]", "UNKNOWN", "NONE"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def to_int(value: Any) -> int | None:
    """Extract an integer from a value, returning None when unavailable."""
    number = to_float(value)
    return int(number) if number is not None else None
