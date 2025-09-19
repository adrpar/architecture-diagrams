from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Eventing"


def define_events(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Eventing", "Event streaming backbone for domain events")
    ev = model["Eventing"]
    _ = ev + Container("Kafka", "Cluster for events", technology="Kafka")
    _ = ev + Container("Schema Registry", "Schemas for events", technology="Confluent")
    return ev


def link_events(model: SystemLandscape) -> None:
    ev = model["Eventing"]
    core = model["Core Banking"]
    pay = model["Payments"]
    rep = model["Reporting"]
    notif = model["Notifications"]
    # Producers
    model.relate(core["Ledger Service"], ev["Kafka"], "Publishes posting events")
    model.relate(pay["Payments API"], ev["Kafka"], "Publishes payment events")
    # Consumers
    model.relate(ev["Kafka"], notif["Event Router"], "Delivers events")
    model.relate(ev["Kafka"], rep["ETL Job"], "Feeds analytics")