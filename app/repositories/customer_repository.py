from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.customer import Customer, CustomerAddress


class CustomerRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        customer_id: int,
    ) -> Customer | None:

        return self.db.scalar(
            select(Customer).where(
                Customer.id == customer_id
            )
        )

    def get_by_user_id(
        self,
        user_id: int,
    ) -> Customer | None:

        return self.db.scalar(
            select(Customer).where(
                Customer.user_id == user_id
            )
        )

    def get_by_customer_number(
        self,
        customer_number: str,
    ) -> Customer | None:

        return self.db.scalar(
            select(Customer).where(
                Customer.customer_number
                == customer_number
            )
        )

    def get_by_email(
        self,
        email: str,
    ) -> Customer | None:

        return self.db.scalar(
            select(Customer).where(
                func.lower(Customer.email)
                == email.lower()
            )
        )

    def get_by_phone(
        self,
        phone: str,
    ) -> Customer | None:

        return self.db.scalar(
            select(Customer).where(
                Customer.phone == phone
            )
        )

    def create(
        self,
        customer: Customer,
    ) -> Customer:

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def update(
        self,
        customer: Customer,
    ) -> Customer:

        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)

        return customer

    def search(
        self,
        search: str | None = None,
        kyc_status=None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Customer], int]:

        query = select(Customer)

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    Customer.customer_number.ilike(
                        pattern
                    ),
                    Customer.full_name.ilike(
                        pattern
                    ),
                    Customer.email.ilike(
                        pattern
                    ),
                    Customer.phone.ilike(
                        pattern
                    ),
                )
            )

        if kyc_status is not None:
            query = query.where(
                Customer.kyc_status == kyc_status
            )

        if is_active is not None:
            query = query.where(
                Customer.is_active == is_active
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(count_query) or 0

        customers = list(
            self.db.scalars(
                query
                .order_by(Customer.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )

        return customers, total

    def create_address(
        self,
        address: CustomerAddress,
    ) -> CustomerAddress:

        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)

        return address

    def get_address(
        self,
        customer_id: int,
        address_id: int,
    ) -> CustomerAddress | None:

        return self.db.scalar(
            select(CustomerAddress).where(
                CustomerAddress.id == address_id,
                CustomerAddress.customer_id == customer_id,
            )
        )

    def get_addresses(
        self,
        customer_id: int,
    ) -> list[CustomerAddress]:

        return list(
            self.db.scalars(
                select(CustomerAddress)
                .where(
                    CustomerAddress.customer_id
                    == customer_id
                )
                .order_by(
                    CustomerAddress.is_primary.desc(),
                    CustomerAddress.id.desc(),
                )
            )
        )

    def update_address(
        self,
        address: CustomerAddress,
    ) -> CustomerAddress:

        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)

        return address

    def delete_address(
        self,
        address: CustomerAddress,
    ) -> None:

        self.db.delete(address)
        self.db.commit()