"""Minimal Crewspan API client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx


class CrewspanAPIError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CrewspanClient:
    """HTTP client for Crewspan REST API."""

    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"X-Tenant-Id": self.tenant_id, "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.request(method, path, headers=self._headers(), **kwargs)
            if response.status_code >= 400:
                raise CrewspanAPIError(response.text, status_code=response.status_code)
            if response.status_code == 204:
                return None
            return response.json()

    def health(self) -> dict[str, str]:
        return self._request("GET", "/health")

    def list_work_orders(self, *, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/work-orders?page={page}&page_size={page_size}")

    def get_work_order(self, work_order_id: str | UUID) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/work-orders/{work_order_id}")

    def create_work_order(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/work-orders", json=data)

    def list_technicians(self, *, page: int = 1) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/technicians?page={page}")

    def list_customers(self, *, page: int = 1) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/customers?page={page}")
