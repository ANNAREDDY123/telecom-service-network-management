from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.customer import KYCStatus
from app.models.user import User, UserRole
from app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerAddressUpdate,
    CustomerCreate,
    CustomerKYCUpdate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService
from app.utils.dependencies import (
    get_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customer Management"],
)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    data: CustomerCreate,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.create_customer(data)


@router.get(
    "",
)
def list_customers(
    search: str | None = Query(
        default=None
    ),
    kyc_status: KYCStatus | None = Query(
        default=None
    ),
    is_active: bool | None = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    skip = (page - 1) * page_size

    customers, total = service.search_customers(
        search=search,
        kyc_status=kyc_status,
        is_active=is_active,
        skip=skip,
        limit=page_size,
    )

    return {
        "items": customers,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (
            (total + page_size - 1)
            // page_size
            if total
            else 0
        ),
    }


@router.get(
    "/me",
    response_model=CustomerResponse,
)
def get_my_customer_profile(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    customer = service.repository.get_by_user_id(
        current_user.id
    )

    if not customer:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    return customer


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
            UserRole.SUPPORT_AGENT,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.get_customer(customer_id)


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.update_customer(
        customer_id,
        data,
    )


@router.patch(
    "/{customer_id}/kyc",
    response_model=CustomerResponse,
)
def update_kyc(
    customer_id: int,
    data: CustomerKYCUpdate,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.update_kyc(
        customer_id,
        data,
    )


@router.patch(
    "/{customer_id}/activate",
    response_model=CustomerResponse,
)
def activate_customer(
    customer_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.set_active_status(
        customer_id,
        True,
    )


@router.patch(
    "/{customer_id}/deactivate",
    response_model=CustomerResponse,
)
def deactivate_customer(
    customer_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.SUPER_ADMIN,
            UserRole.OPERATIONS_MANAGER,
        )
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.set_active_status(
        customer_id,
        False,
    )


@router.post(
    "/{customer_id}/addresses",
    response_model=CustomerAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_address(
    customer_id: int,
    data: CustomerAddressCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    if (
        current_user.role == UserRole.CUSTOMER
        and service.repository.get_by_user_id(
            current_user.id
        ).id
        != customer_id
    ):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customers can only manage their own addresses",
        )

    return service.add_address(
        customer_id,
        data,
    )


@router.get(
    "/{customer_id}/addresses",
    response_model=list[CustomerAddressResponse],
)
def get_addresses(
    customer_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    if current_user.role == UserRole.CUSTOMER:
        customer = service.repository.get_by_user_id(
            current_user.id
        )

        if not customer or customer.id != customer_id:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only view their own addresses",
            )

    return service.get_addresses(customer_id)


@router.put(
    "/{customer_id}/addresses/{address_id}",
    response_model=CustomerAddressResponse,
)
def update_address(
    customer_id: int,
    address_id: int,
    data: CustomerAddressUpdate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    if current_user.role == UserRole.CUSTOMER:
        customer = service.repository.get_by_user_id(
            current_user.id
        )

        if not customer or customer.id != customer_id:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only update their own addresses",
            )

    return service.update_address(
        customer_id,
        address_id,
        data,
    )


@router.delete(
    "/{customer_id}/addresses/{address_id}",
)
def delete_address(
    customer_id: int,
    address_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    if current_user.role == UserRole.CUSTOMER:
        customer = service.repository.get_by_user_id(
            current_user.id
        )

        if not customer or customer.id != customer_id:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only delete their own addresses",
            )

    service.delete_address(
        customer_id,
        address_id,
    )

    return {
        "message": "Address deleted successfully"
    }