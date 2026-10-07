import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from notification_service import OrderHandoff, enqueue_buyer_update


class FakeClient:
    def __init__(self):
        self.queue = None
        self.payload = None

    def queue_publish(self, queue, payload):
        self.queue = queue
        self.payload = payload
        return {"ok": True, "data": {"queued": True}}


def test_order_handoff_is_queued_before_delivery():
    client = FakeClient()
    result = enqueue_buyer_update(client, "buyer-updates", OrderHandoff("o-1", "s-1", "b-1", "ledger.csv"))
    assert result["data"]["queued"] is True
    assert client.queue == "buyer-updates"
    assert client.payload["state"] == "seller_handoff"
    assert client.payload["buyer_id"] == "b-1"
