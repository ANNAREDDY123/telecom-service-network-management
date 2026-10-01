from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import (
    Customer,
    CustomerAddress,
    KYCStatus,
)
from app.models.user import User, UserRole
from app.repositories.customer_repository import (
    CustomerRepository,
)
from app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressUpdate,
    CustomerCreate,
    CustomerKYCUpdate,
    CustomerUpdate,
)


class CustomerService:

    def __init__(self, db: Session):
        self.repository = CustomerRepository(db)
        self.db = db

    def _generate_customer_number(self) -> str:
        return (
            "TEL"
            + uuid4().hex[:10].upper()
        )

    def create_customer(
        self,
        data: CustomerCreate,
    ) -> Customer:

        user = self.db.get(User, data.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.role != UserRole.CUSTOMER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer profile can only be created for a Customer user",
            )

        existing_customer = (
            self.repository.get_by_user_id(
                data.user_id
            )
        )

        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer profile already exists for this user",
            )

        existing_email = (
            self.repository.get_by_email(
                data.email
            )
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer email is already registered",
            )

        existing_phone = (
            self.repository.get_by_phone(
                data.phone
            )
        )

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer phone number is already registered",
            )

        customer = Customer(
            user_id=data.user_id,
            customer_number=self._generate_customer_number(),
            full_name=data.full_name.strip(),
            email=data.email.lower(),
            phone=data.phone,
            alternate_phone=data.alternate_phone,
            kyc_status=KYCStatus.PENDING,
            is_active=True,
        )

        return self.repository.create(customer)

    def get_customer(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.repository.get_by_id(
            customer_id
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    def update_customer(
        self,
        customer_id: int,
        data: CustomerUpdate,
    ) -> Customer:

        customer = self.get_customer(customer_id)

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive customer cannot be updated",
            )

        if data.email is not None:
            existing = self.repository.get_by_email(
                data.email
            )

            if existing and existing.id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer email is already registered",
                )

            customer.email = data.email.lower()

        if data.phone is not None:
            existing = self.repository.get_by_phone(
                data.phone
            )

            if existing and existing.id != customer.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Customer phone number is already registered",
                )

            customer.phone = data.phone

        if data.full_name is not None:
            customer.full_name = data.full_name.strip()

        if data.alternate_phone is not None:
            customer.alternate_phone = data.alternate_phone

        return self.repository.update(customer)

    def update_kyc(
        self,
        customer_id: int,
        data: CustomerKYCUpdate,
    ) -> Customer:

        customer = self.get_customer(customer_id)

        customer.kyc_status = data.kyc_status

        return self.repository.update(customer)

    def set_active_status(
        self,
        customer_id: int,
        is_active: bool,
    ) -> Customer:

        customer = self.get_customer(customer_id)

        customer.is_active = is_active

        return self.repository.update(customer)

    def search_customers(
        self,
        search: str | None = None,
        kyc_status=None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        return self.repository.search(
            search=search,
            kyc_status=kyc_status,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    def add_address(
        self,
        customer_id: int,
        data: CustomerAddressCreate,
    ) -> CustomerAddress:

        customer = self.get_customer(customer_id)

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add address to inactive customer",
            )

        addresses = self.repository.get_addresses(
            customer_id
        )

        if data.is_primary:
            for address in addresses:
                address.is_primary = False

        elif not addresses:
            data.is_primary = True

        address = CustomerAddress(
            customer_id=customer_id,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            address_type=data.address_type,
            is_primary=data.is_primary,
        )

        return self.repository.create_address(
            address
        )

    def get_addresses(
        self,
        customer_id: int,
    ) -> list[CustomerAddress]:

        self.get_customer(customer_id)

        return self.repository.get_addresses(
            customer_id
        )

    def update_address(
        self,
        customer_id: int,
        address_id: int,
        data: CustomerAddressUpdate,
    ) -> CustomerAddress:

        self.get_customer(customer_id)

        address = self.repository.get_address(
            customer_id,
            address_id,
        )

        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        if update_data.get("is_primary") is True:
            addresses = self.repository.get_addresses(
                customer_id
            )

            for existing in addresses:
                existing.is_primary = (
                    existing.id == address_id
                )

        for field, value in update_data.items():
            setattr(address, field, value)

        return self.repository.update_address(
            address
        )

    def delete_address(
        self,
        customer_id: int,
        address_id: int,
    ) -> None:

        self.get_customer(customer_id)

        address = self.repository.get_address(
            customer_id,
            address_id,
        )

        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )

        self.repository.delete_address(address)