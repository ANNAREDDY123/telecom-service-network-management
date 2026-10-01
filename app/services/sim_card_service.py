from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.service_plan import PlanStatus, ServicePlan
from app.models.sim_card import SIMCard, SIMStatus
from app.repositories.sim_card_repository import (
    SIMCardRepository,
)
from app.schemas.sim_card import (
    SIMCardCreate,
    SIMCardUpdate,
    SIMReplacementCreate,
    SIMStatusUpdate,
)


class SIMCardService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = SIMCardRepository(db)

    def get_sim(
        self,
        sim_id: int,
    ) -> SIMCard:

        sim = self.repository.get_by_id(sim_id)

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM card not found",
            )

        return sim

    def validate_customer(
        self,
        customer_id: int,
    ) -> Customer:

        customer = self.db.get(
            Customer,
            customer_id,
        )

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        if not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer account is inactive",
            )

        return customer

    def validate_plan(
        self,
        plan_id: int,
    ) -> ServicePlan:

        plan = self.db.get(
            ServicePlan,
            plan_id,
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service plan not found",
            )

        if plan.status != PlanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service plan is inactive",
            )

        return plan

    def create_sim(
        self,
        data: SIMCardCreate,
    ) -> SIMCard:

        existing = self.repository.get_by_sim_number(
            data.sim_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="SIM number already exists",
            )

        if data.customer_id is not None:
            self.validate_customer(
                data.customer_id
            )

        if data.plan_id is not None:
            self.validate_plan(
                data.plan_id
            )

        if (
            data.customer_id is not None
            and data.plan_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A service plan is required "
                    "when assigning a SIM to a customer"
                ),
            )

        sim = SIMCard(
            sim_number=data.sim_number.strip(),
            sim_type=data.sim_type,
            status=SIMStatus.AVAILABLE,
            customer_id=data.customer_id,
            plan_id=data.plan_id,
        )

        # A newly created SIM assigned to a customer
        # remains Available until explicit activation.
        return self.repository.create(sim)

    def update_sim(
        self,
        sim_id: int,
        data: SIMCardUpdate,
    ) -> SIMCard:

        sim = self.get_sim(sim_id)

        if sim.status in {
            SIMStatus.BLOCKED,
            SIMStatus.DEACTIVATED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Blocked or deactivated SIM "
                    "cannot be updated"
                ),
            )

        if data.customer_id is not None:
            self.validate_customer(
                data.customer_id
            )

        if data.plan_id is not None:
            self.validate_plan(
                data.plan_id
            )

        if (
            data.customer_id is not None
            and data.plan_id is None
            and sim.plan_id is None
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A service plan is required "
                    "when assigning a SIM to a customer"
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(sim, field, value)

        return self.repository.update(sim)

    def activate_sim(
        self,
        sim_id: int,
    ) -> SIMCard:

        sim = self.get_sim(sim_id)

        if sim.status == SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SIM is already active",
            )

        if sim.status not in {
            SIMStatus.AVAILABLE,
            SIMStatus.SUSPENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Available or Suspended "
                    "SIMs can be activated"
                ),
            )

        if sim.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM must be assigned to a customer "
                    "before activation"
                ),
            )

        if sim.plan_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM must have a service plan "
                    "before activation"
                ),
            )

        self.validate_customer(sim.customer_id)
        self.validate_plan(sim.plan_id)

        existing_active = (
            self.repository.get_active_customer_sim(
                sim.customer_id
            )
        )

        if (
            existing_active
            and existing_active.id != sim.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Customer already has an active SIM"
                ),
            )

        sim.status = SIMStatus.ACTIVE
        sim.activation_date = date.today()

        return self.repository.update(sim)

    def update_status(
        self,
        sim_id: int,
        data: SIMStatusUpdate,
    ) -> SIMCard:

        sim = self.get_sim(sim_id)

        new_status = data.status

        if sim.status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"SIM is already "
                    f"{new_status.value}"
                ),
            )

        allowed_transitions = {
            SIMStatus.AVAILABLE: {
                SIMStatus.ACTIVE,
                SIMStatus.BLOCKED,
                SIMStatus.DEACTIVATED,
            },
            SIMStatus.ACTIVE: {
                SIMStatus.SUSPENDED,
                SIMStatus.LOST,
                SIMStatus.BLOCKED,
                SIMStatus.DEACTIVATED,
            },
            SIMStatus.SUSPENDED: {
                SIMStatus.ACTIVE,
                SIMStatus.BLOCKED,
                SIMStatus.DEACTIVATED,
            },
            SIMStatus.LOST: {
                SIMStatus.BLOCKED,
                SIMStatus.DEACTIVATED,
            },
            SIMStatus.BLOCKED: {
                SIMStatus.DEACTIVATED,
            },
            SIMStatus.DEACTIVATED: set(),
        }

        if new_status not in allowed_transitions.get(
            sim.status,
            set(),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid SIM status transition: "
                    f"{sim.status.value} -> "
                    f"{new_status.value}"
                ),
            )

        if new_status == SIMStatus.ACTIVE:
            return self.activate_sim(sim_id)

        sim.status = new_status

        return self.repository.update(sim)

    def replace_sim(
        self,
        sim_id: int,
        data: SIMReplacementCreate,
    ) -> tuple[SIMCard, SIMCard]:

        old_sim = self.get_sim(sim_id)

        if old_sim.status not in {
            SIMStatus.ACTIVE,
            SIMStatus.LOST,
            SIMStatus.SUSPENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Active, Lost, or Suspended "
                    "SIMs can be replaced"
                ),
            )

        existing = self.repository.get_by_sim_number(
            data.new_sim_number
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="New SIM number already exists",
            )

        if data.plan_id is not None:
            self.validate_plan(data.plan_id)

        old_customer_id = old_sim.customer_id

        if old_customer_id is not None:
            self.validate_customer(old_customer_id)

        new_sim = SIMCard(
            sim_number=data.new_sim_number.strip(),
            sim_type=data.sim_type,
            status=SIMStatus.AVAILABLE,
            customer_id=old_customer_id,
            plan_id=(
                data.plan_id
                if data.plan_id is not None
                else old_sim.plan_id
            ),
            replacement_of_sim_id=old_sim.id,
            replacement_reason=data.reason,
        )

        old_sim.status = SIMStatus.DEACTIVATED

        self.db.add(old_sim)
        self.db.add(new_sim)
        self.db.commit()
        self.db.refresh(old_sim)
        self.db.refresh(new_sim)

        return old_sim, new_sim

    def search_sims(
        self,
        search: str | None = None,
        sim_type=None,
        sim_status=None,
        customer_id: int | None = None,
        plan_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        return self.repository.search(
            search=search,
            sim_type=sim_type,
            sim_status=sim_status,
            customer_id=customer_id,
            plan_id=plan_id,
            skip=skip,
            limit=limit,
        )