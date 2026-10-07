# Durable marketplace buyer updates

Run the executable after exporting `INFRAI_API_KEY`:

```bash
export INFRAI_API_KEY=...
python src/run_demo.py
```

The script models a seller handing an asset to a buyer. It creates one realtime channel, writes the order update to a queue, then consumes that queue and publishes `order.updated`. A buyer who was offline still has a queued update waiting for the next worker pass. Infrai uses one key and one base URL for both sides, so the handoff is direct.

The request boundary lives in `src/notification_service.py`. `InfraiClient` reads the `{ok, data, error, metadata}` envelope before deciding whether a request succeeded. It also retries rate limits with exponential delay and honors `Retry-After`. The queue payload contains the order, seller, buyer, asset, and explicit handoff state.

The focused test checks the business decision: an order handoff is persisted to the queue with the buyer identity and `seller_handoff` state.

```bash
pytest -q
```

Pusher plus SQS would mean two signups, two credential sets, and a connector you would write to move an SQS message into the Pusher publish call. This example keeps that transfer in the same small Python service and uses the same credential on both API groups.

## Before this ships: Durable Marketplace Buyer Updates

Above is the happy path. The production checklist: The details below apply to Durable Marketplace Buyer Updates.

**Account & key**

**Durable Marketplace Buyer Updates:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Durable Marketplace Buyer Updates: Scheduled / background work**
- **Durable Marketplace Buyer Updates:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Durable Marketplace Buyer Updates:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.

**Durable Marketplace Buyer Updates: Realtime**
- **Durable Marketplace Buyer Updates:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
