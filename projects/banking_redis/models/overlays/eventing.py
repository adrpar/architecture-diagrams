from __future__ import annotations

import logging
from typing import Any


def apply(model: Any) -> None:
    # Replace Kafka with Redis Queue, tag changes
    res = model.replace_container_report(
        "Eventing",
        "Kafka",
        "Redis Queue",
        description="Queue for events",
        technology="Redis Streams",
        tag_new={"proposed", "database"},
        tag_old={"deprecated"},
        remove_old=False,  # keep Kafka node so Delta view can visualize change
    )
    logging.getLogger(__name__).debug(
        "overlay.eventing: replaced '%s' -> '%s' (created_new=%s, rewired=%d, removed_old=%s)",
        getattr(res.old_container, "name", None),
        res.new_container.name,
        res.created_new,
        res.rewired_count,
        res.removed_old,
    )
