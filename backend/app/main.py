from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import alerts, connectors, detections, events, health, ingests, metrics, sources


app = FastAPI(
    title="CBRN-E Intelligence Lab API",
    version="0.1.0",
    description="Evidence-linked threat indication and warning workflow API.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(sources.router)
app.include_router(connectors.router)
app.include_router(ingests.router)
app.include_router(events.router)
app.include_router(detections.router)
app.include_router(alerts.router)
app.include_router(metrics.router)
