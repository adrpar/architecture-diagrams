from architecture_diagrams.c4 import Container, SoftwareSystem, SystemLandscape

SYSTEM_KEY = "Risk & ML"


def define_ml_risk(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Risk & ML", "Model training, feature store, and inference services")
    ml = model["Risk & ML"]
    _ = ml + Container("Feature Store", "Aggregated features for models", technology="Feast")
    _ = ml + Container("Model Serving", "Online inference APIs", technology="Python")
    _ = ml + Container("Training Pipeline", "Offline model training", technology="Python")
    return ml


def link_ml_risk(model: SystemLandscape) -> None:
    ml = model["Risk & ML"]
    pay = model["Payments"]
    rep = model["Reporting"]
    # Payments Fraud Service calls model serving; training consumes data from Reporting
    model.relate(pay["Fraud Service"], ml["Model Serving"], "Requests fraud scores")
    model.relate(ml["Training Pipeline"], rep["ETL Job"], "Consumes historical data")
    model.relate(ml["Feature Store"], ml["Model Serving"], "Provides features")
