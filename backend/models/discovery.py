"""Fetch available models from an OpenAI-compatible endpoint."""
from __future__ import annotations
import logging

import httpx

logger = logging.getLogger(__name__)


async def fetch_models(base_url: str, api_key: str) -> list[str]:
    """Fetch available model IDs from the /v1/models endpoint."""
    url = base_url.rstrip("/") + "/models"
    headers = {}
    if api_key and api_key.lower() != "none":
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", [])
            return sorted([m["id"] for m in models if "id" in m])
    except Exception as e:
        logger.warning(f"Could not fetch models from {url}: {e}")
        return []
