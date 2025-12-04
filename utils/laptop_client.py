"""
Client utilities for talking to the FaceTimeOS backend running on the Mac.

This module is responsible for:
- Reading laptop backend config (host/port/timeout) from the main config dict.
- Sending text tasks to the Mac's `/pi_task` endpoint.
- Optionally downloading screenshots returned by the backend.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests


logger = logging.getLogger(__name__)


@dataclass
class LaptopBackendConfig:
    host: str
    port: int
    timeout_seconds: float = 300.0  # 5 minutes - allow complex tasks to complete

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "LaptopBackendConfig":
        laptop_cfg = config.get("laptop", {}) or {}
        host = str(laptop_cfg.get("host") or "localhost")
        port = int(laptop_cfg.get("port") or 8000)
        timeout = float(laptop_cfg.get("timeout_seconds") or 300.0)  # Default 5 minutes
        return cls(host=host, port=port, timeout_seconds=timeout)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def send_laptop_task(
    backend_cfg: LaptopBackendConfig,
    task_id: str,
    user_text: str,
    mode: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send a natural-language task to the Mac's /pi_task endpoint.

    Returns a normalized dict with status, message, and optional screenshot_url.
    """
    if not user_text or not user_text.strip():
        raise ValueError("user_text is required")

    payload: Dict[str, Any] = {
        "task_id": task_id,
        "user_text": user_text.strip(),
        "mode": mode,
        "options": options or {"send_screenshot": True},
    }

    url = f"{backend_cfg.base_url}/pi_task"
    logger.info("Sending laptop task to %s: %s", url, payload)
    print(f"📤 Sending task to backend (waiting for completion, no timeout)...")

    try:
        # Wait indefinitely until task completes (done or failed)
        print(f"   Waiting for task to complete (no timeout - will wait until done/failed)...")
        response = requests.post(url, json=payload, timeout=None)
        print(f"✅ Received response from backend: status={response.status_code}, size={len(response.content)} bytes")
    except requests.RequestException as exc:
        logger.error("Failed to reach laptop backend: %s", exc, exc_info=True)
        return {
            "task_id": task_id,
            "status": "error",
            "message": f"Could not reach laptop backend: {exc}",
            "screenshot_url": None,
        }

    try:
        data = response.json()
    except ValueError:
        logger.warning("Non-JSON response from laptop backend: %s", response.text[:200])
        return {
            "task_id": task_id,
            "status": "error",
            "message": "Laptop backend returned non-JSON response",
            "screenshot_url": None,
        }

    # Normalize fields
    status = data.get("status", "unknown")
    message = data.get("message") or ""
    screenshot_url = data.get("screenshot_url")

    return {
        "task_id": data.get("task_id", task_id),
        "status": status,
        "message": message,
        "screenshot_url": screenshot_url,
    }


def download_screenshot(url: str, dest_dir: Path) -> Optional[Path]:
    """
    Download a screenshot from the given URL into dest_dir.

    Returns the local Path if successful, otherwise None.
    """
    if not url:
        return None

    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1] or "screenshot.png"
    dest_path = dest_dir / filename

    logger.info("Downloading screenshot from %s to %s", url, dest_path)

    try:
        response = requests.get(url, timeout=float(os.getenv("SCREENSHOT_DOWNLOAD_TIMEOUT", "30")))
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to download screenshot: %s", exc, exc_info=True)
        return None

    try:
        dest_path.write_bytes(response.content)
        return dest_path
    except OSError as exc:
        logger.error("Failed to write screenshot to %s: %s", dest_path, exc)
        return None


