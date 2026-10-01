from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.service_request import (
    ServiceRequest,
    ServiceRequestPriority,
    ServiceRequestStatus,
    ServiceRequestType,
)


class ServiceRequestRepository:

    @staticmethod
    def get_by_id(
        db: Session,
        request_id: int,
    ) -> ServiceRequest | None:
        return db.get(ServiceRequest, request_id)

    @staticmethod
    def get_by_request_number(
        db: Session,
        request_number: str,
    ) -> ServiceRequest | None:
        return db.scalar(
            select(ServiceRequest).where(
                ServiceRequest.request_number == request_number
            )
        )

    @staticmethod
    def create(
        db: Session,
        service_request: ServiceRequest,
    ) -> ServiceRequest:
        db.add(service_request)
        db.flush()
        db.refresh(service_request)
        return service_request

    @staticmethod
    def update(
        db: Session,
        service_request: ServiceRequest,
    ) -> ServiceRequest:
        db.flush()
        db.refresh(service_request)
        return service_request

    @staticmethod
    def list(
        db: Session,
        *,
        page: int,
        page_size: int,
        customer_id: int | None = None,
        request_type: ServiceRequestType | None = None,
        priority: ServiceRequestPriority | None = None,
        status: ServiceRequestStatus | None = None,
        search: str | None = None,
    ) -> list[ServiceRequest]:

        query = select(ServiceRequest)

        if customer_id is not None:
            query = query.where(
                ServiceRequest.customer_id == customer_id
            )

        if request_type is not None:
            query = query.where(
                ServiceRequest.request_type == request_type
            )

        if priority is not None:
            query = query.where(
                ServiceRequest.priority == priority
            )

        if status is not None:
            query = query.where(
                ServiceRequest.status == status
            )

        if search:
            search_value = f"%{search.strip()}%"

            query = query.where(
                or_(
                    ServiceRequest.request_number.ilike(search_value),
                    ServiceRequest.title.ilike(search_value),
                    ServiceRequest.description.ilike(search_value),
                )
            )

        query = query.order_by(
            ServiceRequest.created_at.desc()
        )

        query = query.offset(
            (page - 1) * page_size
        ).limit(page_size)

        return list(db.scalars(query).all())

    @staticmethod
    def count(
        db: Session,
        *,
        customer_id: int | None = None,
        request_type: ServiceRequestType | None = None,
        priority: ServiceRequestPriority | None = None,
        status: ServiceRequestStatus | None = None,
        search: str | None = None,
    ) -> int:

        query = select(
            func.count(ServiceRequest.id)
        )

        if customer_id is not None:
            query = query.where(
                ServiceRequest.customer_id == customer_id
            )

        if request_type is not None:
            query = query.where(
                ServiceRequest.request_type == request_type
            )

        if priority is not None:
            query = query.where(
                ServiceRequest.priority == priority
            )

        if status is not None:
            query = query.where(
                ServiceRequest.status == status
            )

        if search:
            search_value = f"%{search.strip()}%"

            query = query.where(
                or_(
                    ServiceRequest.request_number.ilike(search_value),
                    ServiceRequest.title.ilike(search_value),
                    ServiceRequest.description.ilike(search_value),
                )
            )

        return db.scalar(query) or 0