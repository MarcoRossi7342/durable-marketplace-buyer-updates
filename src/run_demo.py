import os

from notification_service import InfraiClient, OrderHandoff, enqueue_buyer_update, fanout_queued_updates


def main() -> None:
    client = InfraiClient()
    channel = "marketplace-buyer-updates"
    queue = "marketplace-buyer-updates"
    client.create_channel(channel)
    handoff = OrderHandoff("order-1042", "seller-7", "buyer-19", "etl-course.zip")
    enqueue_buyer_update(client, queue, handoff)
    delivered = fanout_queued_updates(client, queue, channel, os.environ.get("INFRAI_ACCOUNT_ID", "marketplace-demo"))
    print({"channel": channel, "queued_order": handoff.order_id, "delivered": delivered})


if __name__ == "__main__":
    main()
