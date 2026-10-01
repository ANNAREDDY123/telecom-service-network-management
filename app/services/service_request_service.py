from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestPriority,
    ServiceRequestStatus,
    ServiceRequestType,
)
from app.models.user import User, UserRole
from app.repositories.service_request_repository import (
    ServiceRequestRepository,
)
from app.schemas.service_request import (
    ServiceRequestCompletion,
    ServiceRequestCreate,
    ServiceRequestRejection,
    ServiceRequestStatusUpdate,
    ServiceRequestUpdate,
)


class ServiceRequestService:

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _validate_pagination(
        page: int,
        page_size: int,
    ) -> None:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than or equal to 1",
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100",
            )

    @staticmethod
    def _get_customer(
        db: Session,
        customer_id: int,
    ) -> Customer:
        customer = db.get(Customer, customer_id)

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive customer cannot create service requests",
            )

        return customer

    @staticmethod
    def _get_request(
        db: Session,
        request_id: int,
    ) -> ServiceRequest:
        service_request = ServiceRequestRepository.get_by_id(
            db,
            request_id,
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        return service_request

    @staticmethod
    def _ensure_modifiable(
        service_request: ServiceRequest,
    ) -> None:
        terminal_statuses = {
            ServiceRequestStatus.COMPLETED,
            ServiceRequestStatus.CANCELLED,
            ServiceRequestStatus.REJECTED,
        }

        if service_request.status in terminal_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Completed, cancelled, or rejected service "
                    "requests cannot be modified"
                ),
            )

    @staticmethod
    def _validate_related_entities(
        db: Session,
        data: ServiceRequestCreate,
    ) -> None:
        if data.subscription_id is not None:
            from app.models.subscription import Subscription

            subscription = db.get(
                Subscription,
                data.subscription_id,
            )

            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Subscription not found",
                )

            if subscription.customer_id != data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subscription does not belong to customer",
                )

        if data.sim_card_id is not None:
            from app.models.sim_card import SIMCard

            sim_card = db.get(
                SIMCard,
                data.sim_card_id,
            )

            if not sim_card:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SIM card not found",
                )

            if sim_card.customer_id != data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SIM card does not belong to customer",
                )

        if data.device_id is not None:
            from app.models.device import Device

            device = db.get(
                Device,
                data.device_id,
            )

            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Device not found",
                )

            if device.customer_id != data.customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Device does not belong to customer",
                )

    @staticmethod
    def create(
        db: Session,
        data: ServiceRequestCreate,
    ) -> ServiceRequest:

        ServiceRequestService._get_customer(
            db,
            data.customer_id,
        )

        existing = ServiceRequestRepository.get_by_request_number(
            db,
            data.request_number,
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Service request number already exists",
            )

        ServiceRequestService._validate_related_entities(
            db,
            data,
        )

        service_request = ServiceRequest(
            request_number=data.request_number.strip(),
            customer_id=data.customer_id,
            subscription_id=data.subscription_id,
            sim_card_id=data.sim_card_id,
            device_id=data.device_id,
            request_type=data.request_type,
            priority=data.priority,
            status=ServiceRequestStatus.SUBMITTED,
            title=data.title.strip(),
            description=data.description.strip(),
            submitted_at=ServiceRequestService._utc_now(),
        )

        return ServiceRequestRepository.create(
            db,
            service_request,
        )

    @staticmethod
    def get(
        db: Session,
        request_id: int,
    ) -> ServiceRequest:
        return ServiceRequestService._get_request(
            db,
            request_id,
        )

    @staticmethod
    def update(
        db: Session,
        request_id: int,
        data: ServiceRequestUpdate,
    ) -> ServiceRequest:

        service_request = ServiceRequestService._get_request(
            db,
            request_id,
        )

        ServiceRequestService._ensure_modifiable(
            service_request,
        )

        if data.priority is not None:
            service_request.priority = data.priority

        if data.title is not None:
            service_request.title = data.title.strip()

        if data.description is not None:
            service_request.description = data.description.strip()

        if data.processing_notes is not None:
            service_request.processing_notes = (
                data.processing_notes.strip()
            )

        return ServiceRequestRepository.update(
            db,
            service_request,
        )

    @staticmethod
    def update_status(
        db: Session,
        request_id: int,
        data: ServiceRequestStatusUpdate,
        current_user: User,
    ) -> ServiceRequest:

        service_request = ServiceRequestService._get_request(
            db,
            request_id,
        )

        current = ServiceRequestStatus(
            service_request.status
        )

        target = data.status

        if current == target:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service request is already in this status",
            )

        transitions = {
            ServiceRequestStatus.SUBMITTED: {
                ServiceRequestStatus.UNDER_REVIEW,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.UNDER_REVIEW: {
                ServiceRequestStatus.APPROVED,
                ServiceRequestStatus.REJECTED,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.APPROVED: {
                ServiceRequestStatus.IN_PROGRESS,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.IN_PROGRESS: {
                ServiceRequestStatus.COMPLETED,
                ServiceRequestStatus.CANCELLED,
            },
            ServiceRequestStatus.REJECTED: set(),
            ServiceRequestStatus.COMPLETED: set(),
            ServiceRequestStatus.CANCELLED: set(),
        }

        allowed = transitions.get(current, set())

        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition: "
                    f"{current.value} -> {target.value}"
                ),
            )

        now = ServiceRequestService._utc_now()

        if target == ServiceRequestStatus.UNDER_REVIEW:
            service_request.reviewed_at = now

        elif target == ServiceRequestStatus.APPROVED:
            service_request.approved_at = now

        elif target == ServiceRequestStatus.REJECTED:
            service_request.rejected_at = now

        elif target == ServiceRequestStatus.IN_PROGRESS:
            service_request.started_at = now

        elif target == ServiceRequestStatus.COMPLETED:
            service_request.completed_at = now

        elif target == ServiceRequestStatus.CANCELLED:
            service_request.cancelled_at = now

        if data.notes:
            if target == ServiceRequestStatus.COMPLETED:
                service_request.completed_notes = data.notes.strip()
            else:
                service_request.processing_notes = data.notes.strip()

        service_request.status = target

        return ServiceRequestRepository.update(
            db,
            service_request,
        )

    @staticmethod
    def approve(
        db: Session,
        request_id: int,
        current_user: User,
    ) -> ServiceRequest:

        if current_user.role not in {
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorized operations roles can approve requests",
            )

        return ServiceRequestService.update_status(
            db,
            request_id,
            ServiceRequestStatusUpdate(
                status=ServiceRequestStatus.APPROVED
            ),
            current_user,
        )

    @staticmethod
    def reject(
        db: Session,
        request_id: int,
        data: ServiceRequestRejection,
        current_user: User,
    ) -> ServiceRequest:

        if current_user.role not in {
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only authorized operations roles can reject requests",
            )

        service_request = ServiceRequestService._get_request(
            db,
            request_id,
        )

        if service_request.status != ServiceRequestStatus.UNDER_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only requests under review can be rejected",
            )

        service_request.rejection_reason = (
            data.rejection_reason.strip()
        )

        service_request.rejected_at = (
            ServiceRequestService._utc_now()
        )

        service_request.status = ServiceRequestStatus.REJECTED

        return ServiceRequestRepository.update(
            db,
            service_request,
        )

    @staticmethod
    def complete(
        db: Session,
        request_id: int,
        data: ServiceRequestCompletion,
        current_user: User,
    ) -> ServiceRequest:

        service_request = ServiceRequestService._get_request(
            db,
            request_id,
        )

        if current_user.role not in {
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
            UserRole.NETWORK_ENGINEER,
            UserRole.FIELD_TECHNICIAN,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not authorized to complete service requests",
            )

        if service_request.status != ServiceRequestStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only in-progress requests can be completed",
            )

        service_request.status = ServiceRequestStatus.COMPLETED
        service_request.completed_at = (
            ServiceRequestService._utc_now()
        )

        if data.completed_notes:
            service_request.completed_notes = (
                data.completed_notes.strip()
            )

        return ServiceRequestRepository.update(
            db,
            service_request,
        )

    @staticmethod
    def cancel(
        db: Session,
        request_id: int,
        current_user: User,
    ) -> ServiceRequest:

        service_request = ServiceRequestService._get_request(
            db,
            request_id,
        )

        if service_request.status in {
            ServiceRequestStatus.COMPLETED,
            ServiceRequestStatus.CANCELLED,
            ServiceRequestStatus.REJECTED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service request cannot be cancelled",
            )

        service_request.status = ServiceRequestStatus.CANCELLED
        service_request.cancelled_at = (
            ServiceRequestService._utc_now()
        )

        return ServiceRequestRepository.update(
            db,
            service_request,
        )

    @staticmethod
    def list(
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        customer_id: int | None = None,
        request_type: ServiceRequestType | None = None,
        priority: ServiceRequestPriority | None = None,
        status_filter: ServiceRequestStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[ServiceRequest], int]:

        ServiceRequestService._validate_pagination(
            page,
            page_size,
        )

        items = ServiceRequestRepository.list(
            db,
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            request_type=request_type,
            priority=priority,
            status=status_filter,
            search=search,
        )

        total = ServiceRequestRepository.count(
            db,
            customer_id=customer_id,
            request_type=request_type,
            priority=priority,
            status=status_filter,
            search=search,
        )

        return items, total

    @staticmethod
    def list_response(
        db: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        customer_id: int | None = None,
        request_type: ServiceRequestType | None = None,
        priority: ServiceRequestPriority | None = None,
        status_filter: ServiceRequestStatus | None = None,
        search: str | None = None,
    ) -> dict:

        items, total = ServiceRequestService.list(
            db,
            page=page,
            page_size=page_size,
            customer_id=customer_id,
            request_type=request_type,
            priority=priority,
            status_filter=status_filter,
            search=search,
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": ceil(total / page_size) if total else 0,
        }