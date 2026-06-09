"""HTTP client for the Go lifecycle controller."""

from __future__ import annotations

import httpx


class ControllerClient:
    """Thin client over the controller's REST API."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ControllerClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def health(self) -> bool:
        try:
            return self._client.get("/health").status_code == 200
        except httpx.HTTPError:
            return False

    def create_intent(self, intent_type: str, params: dict) -> dict:
        resp = self._client.post("/api/v1/intents", json={"intent_type": intent_type, "params": params})
        resp.raise_for_status()
        return resp.json()

    def process(self, intent_id: str) -> dict:
        resp = self._client.post(f"/api/v1/intents/{intent_id}/process")
        resp.raise_for_status()
        return resp.json()

    def get_intent(self, intent_id: str) -> dict:
        resp = self._client.get(f"/api/v1/intents/{intent_id}")
        resp.raise_for_status()
        return resp.json()

    def get_events(self, intent_id: str) -> list[dict]:
        resp = self._client.get(f"/api/v1/intents/{intent_id}/events")
        resp.raise_for_status()
        return resp.json().get("events", [])
