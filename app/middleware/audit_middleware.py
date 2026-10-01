import uuid

import jwt
from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.audit_log import AuditLog


AUDITED_METHODS = {
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}


def extract_user_id_from_token(
    authorization_header: str | None,
) -> int | None:

    if not authorization_header:
        return None

    if not authorization_header.startswith(
        "Bearer "
    ):
        return None

    token = authorization_header[7:].strip()

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")

    if not user_id:
        return None

    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def get_resource_name(
    path: str,
) -> str:

    parts = [
        part
        for part in path.split("/")
        if part
    ]

    if not parts:
        return "system"

    return parts[0]


def get_resource_id(
    path: str,
) -> int | None:

    parts = [
        part
        for part in path.split("/")
        if part
    ]

    for part in reversed(parts):
        try:
            return int(part)
        except ValueError:
            continue

    return None


def get_action(
    method: str,
) -> str:

    actions = {
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }

    return actions.get(
        method.upper(),
        method.upper(),
    )


async def audit_request(
    request: Request,
    call_next,
):

    if request.method.upper() not in AUDITED_METHODS:
        return await call_next(request)

    if request.url.path.startswith(
        "/audit-logs"
    ):
        return await call_next(request)

    request_id = request.headers.get(
        "X-Request-ID"
    ) or str(uuid.uuid4())

    try:
        response = await call_next(request)
    except Exception:
        response = None

        db: Session = SessionLocal()

        try:
            audit_log = AuditLog(
                user_id=extract_user_id_from_token(
                    request.headers.get(
                        "Authorization"
                    )
                ),
                action=get_action(
                    request.method
                ),
                resource=get_resource_name(
                    request.url.path
                ),
                resource_id=get_resource_id(
                    request.url.path
                ),
                method=request.method.upper(),
                endpoint=str(
                    request.url.path
                ),
                status_code=500,
                ip_address=(
                    request.client.host
                    if request.client
                    else None
                ),
                user_agent=request.headers.get(
                    "User-Agent"
                ),
                request_id=request_id,
                details="Unhandled application exception",
            )

            db.add(audit_log)
            db.commit()

        except Exception:
            db.rollback()

        finally:
            db.close()

        raise

    db: Session = SessionLocal()

    try:
        audit_log = AuditLog(
            user_id=extract_user_id_from_token(
                request.headers.get(
                    "Authorization"
                )
            ),
            action=get_action(
                request.method
            ),
            resource=get_resource_name(
                request.url.path
            ),
            resource_id=get_resource_id(
                request.url.path
            ),
            method=request.method.upper(),
            endpoint=str(
                request.url.path
            ),
            status_code=response.status_code,
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
            user_agent=request.headers.get(
                "User-Agent"
            ),
            request_id=request_id,
            details=None,
        )

        db.add(audit_log)
        db.commit()

    except Exception:
        db.rollback()

    finally:
        db.close()

    response.headers[
        "X-Request-ID"
    ] = request_id

    return response