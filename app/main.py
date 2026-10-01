from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.customers import router as customer_router
from app.api.service_plans import router as service_plan_router
from app.api.sim_cards import router as sim_cards_router
from app.api.devices import router as devices_router
from app.api.usage import router as usage_router

from app.api.network_towers import (
    router as network_towers_router,
)
from app.api.subscriptions import (
    router as subscriptions_router,
)
from app.api.network_equipment import (
    router as network_equipment_router,
)
from app.api.network_outages import (
    router as network_outages_router,
)
from app.api.field_technicians import (
    router as field_technicians_router,
)
from app.api.support_tickets import (
    router as support_tickets_router,
)
from app.api.ticket_assignments import (
    router as ticket_assignment_router,
)
from app.api.sla import router as sla_router
from app.api.service_requests import (
    router as service_requests_router,
)
from app.api.notifications import (
    router as notifications_router,
)

from app.api.dashboard import (
    router as dashboard_router,
)
from app.api.reports import (
    router as reports_router,
)
from app.api.audit_logs import (
    router as audit_logs_router,
)
from app.api.system import (
    router as system_router,
)

from app.core.config import settings
from app.core.security_config import (
    security_config,
)

from app.db.database import (
    Base,
    engine,
)
from app.db.performance_indexes import (
    create_performance_indexes,
)

from app.middleware.audit_middleware import (
    audit_request,
)
from app.middleware.security_middleware import (
    security_middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables.
    Base.metadata.create_all(
        bind=engine
    )

    # Create additional composite indexes used by
    # reporting, audit, usage and support queries.
    create_performance_indexes(
        engine
    )

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-oriented Telecom Service & "
        "Network Management System"
    ),
    lifespan=lifespan,
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        security_config.allowed_origins
    ),
    allow_credentials=True,
    allow_methods=list(
        security_config.allowed_methods
    ),
    allow_headers=list(
        security_config.allowed_headers
    ),
)


# ============================================================
# SECURITY MIDDLEWARE
# ============================================================

app.middleware(
    "http"
)(security_middleware)


# ============================================================
# AUDIT MIDDLEWARE
# ============================================================

app.middleware(
    "http"
)(audit_request)


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(
    auth_router
)

app.include_router(
    customer_router
)

app.include_router(
    service_plan_router
)

app.include_router(
    sim_cards_router
)

app.include_router(
    devices_router
)

app.include_router(
    subscriptions_router
)

app.include_router(
    usage_router
)

app.include_router(
    network_towers_router
)

app.include_router(
    network_equipment_router
)

app.include_router(
    network_outages_router
)

app.include_router(
    field_technicians_router
)

app.include_router(
    support_tickets_router
)

app.include_router(
    ticket_assignment_router
)

app.include_router(
    sla_router
)

app.include_router(
    service_requests_router
)

app.include_router(
    notifications_router
)

app.include_router(
    reports_router
)

app.include_router(
    dashboard_router
)

app.include_router(
    audit_logs_router
)

app.include_router(
    system_router
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["System"],
)
def root():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }