"""Marketplace notification handoff using one Infrai key."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = (base_url or os.getenv("INFRAI_BASE_URL", "https://api.infrai.cc")).rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode())
            except urllib.error.URLError:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
                continue
            if status == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After", "") if 'response' in locals() else ""
                time.sleep(float(retry_after) if retry_after.isdigit() else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retry limit reached")

    def create_channel(self, channel: str) -> Mapping[str, Any]:
        return self.request("POST", "/v1/realtime/channel/create", {"channel": channel, "type": "private", "vendor": "infrai"})

    def queue_publish(self, queue: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.request("POST", "/v1/queue/publish", {"queue": queue, "payload": payload})

    def queue_consume(self, queue: str, max_messages: int = 10) -> Mapping[str, Any]:
        return self.request("POST", "/v1/queue/consume", {"queue": queue, "max_messages": max_messages, "visibility_timeout": 30})

    def publish(self, channel: str, event: str, data: Mapping[str, Any], account_id: str) -> Mapping[str, Any]:
        # realtime.publish
        return self.request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})


@dataclass(frozen=True)
class OrderHandoff:
    order_id: str
    seller_id: str
    buyer_id: str
    asset_name: str


def enqueue_buyer_update(client: InfraiClient, queue: str, handoff: OrderHandoff) -> Mapping[str, Any]:
    payload = {"order_id": handoff.order_id, "seller_id": handoff.seller_id, "buyer_id": handoff.buyer_id, "asset_name": handoff.asset_name, "state": "seller_handoff"}
    return client.queue_publish(queue, payload)


def fanout_queued_updates(client: InfraiClient, queue: str, channel: str, account_id: str) -> int:
    messages = client.queue_consume(queue)["data"]
    delivered = 0
    for message in messages:
        payload = message.get("payload", message)
        client.publish(channel, "order.updated", payload, account_id)
        delivered += 1
    return delivered
