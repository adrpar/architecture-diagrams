from __future__ import annotations


def apply(model) -> None:
    # Replace Kafka with Redis Queue, tag changes
    model.replace_container(
        "Eventing",
        "Kafka",
        "Redis Queue",
        description="Queue for events",
        technology="Redis Streams",
        tag_new={"proposed", "database"},
        tag_old={"deprecated"},
        remove_old=False,  # keep Kafka node so Delta view can visualize change
    )
