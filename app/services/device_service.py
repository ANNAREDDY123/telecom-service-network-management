from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.device import Device, DeviceStatus
from app.models.sim_card import SIMCard, SIMStatus
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import (
    DeviceCreate,
    DeviceReplacementCreate,
    DeviceStatusUpdate,
    DeviceUpdate,
)


class DeviceService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = DeviceRepository(db)

    def get_device(
        self,
        device_id: int,
    ) -> Device:

        device = self.repository.get_by_id(device_id)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )

        return device

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

    def validate_sim(
        self,
        sim_id: int,
    ) -> SIMCard:

        sim = self.db.get(
            SIMCard,
            sim_id,
        )

        if not sim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SIM card not found",
            )

        if sim.status in {
            SIMStatus.BLOCKED,
            SIMStatus.DEACTIVATED,
            SIMStatus.LOST,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Blocked, deactivated, or lost "
                    "SIM cannot be assigned to a device"
                ),
            )

        return sim

    def create_device(
        self,
        data: DeviceCreate,
    ) -> Device:

        imei = data.imei.strip()

        existing = self.repository.get_by_imei(imei)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="IMEI already registered",
            )

        if data.customer_id is not None:
            self.validate_customer(
                data.customer_id
            )

        if data.sim_id is not None:
            sim = self.validate_sim(
                data.sim_id
            )

            if (
                data.customer_id is not None
                and sim.customer_id is not None
                and sim.customer_id != data.customer_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SIM is assigned to a different customer"
                    ),
                )

            existing_device = (
                self.repository.get_by_sim_id(
                    data.sim_id
                )
            )

            if existing_device:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "SIM is already assigned to another device"
                    ),
                )

        device = Device(
            imei=imei,
            device_name=data.device_name.strip(),
            manufacturer=data.manufacturer.strip(),
            model_number=data.model_number.strip(),
            device_type=data.device_type,
            status=DeviceStatus.REGISTERED,
            customer_id=data.customer_id,
            sim_id=data.sim_id,
            purchase_date=data.purchase_date,
            warranty_expiry_date=data.warranty_expiry_date,
        )

        return self.repository.create(device)

    def update_device(
        self,
        device_id: int,
        data: DeviceUpdate,
    ) -> Device:

        device = self.get_device(device_id)

        if device.status in {
            DeviceStatus.BLOCKED,
            DeviceStatus.DEACTIVATED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Blocked or deactivated device "
                    "cannot be updated"
                ),
            )

        if data.customer_id is not None:
            self.validate_customer(
                data.customer_id
            )

        if data.sim_id is not None:
            sim = self.validate_sim(
                data.sim_id
            )

            if (
                data.customer_id is not None
                and sim.customer_id is not None
                and sim.customer_id != data.customer_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SIM is assigned to a different customer"
                    ),
                )

            existing_device = (
                self.repository.get_by_sim_id(
                    data.sim_id
                )
            )

            if (
                existing_device
                and existing_device.id != device.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "SIM is already assigned to another device"
                    ),
                )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():

            if isinstance(value, str):
                value = value.strip()

            setattr(
                device,
                field,
                value,
            )

        return self.repository.update(device)

    def activate_device(
        self,
        device_id: int,
    ) -> Device:

        device = self.get_device(device_id)

        if device.status == DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device is already active",
            )

        if device.status not in {
            DeviceStatus.REGISTERED,
            DeviceStatus.SUSPENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Registered or Suspended "
                    "devices can be activated"
                ),
            )

        if device.customer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Device must be assigned to a customer "
                    "before activation"
                ),
            )

        if device.sim_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Device must have a SIM card "
                    "before activation"
                ),
            )

        self.validate_customer(
            device.customer_id
        )

        sim = self.validate_sim(
            device.sim_id
        )

        if (
            sim.customer_id is not None
            and sim.customer_id != device.customer_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM and device belong to different customers"
                ),
            )

        if sim.status != SIMStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "SIM must be active before "
                    "device activation"
                ),
            )

        existing_device = (
            self.repository.get_active_customer_device(
                device.customer_id
            )
        )

        if (
            existing_device
            and existing_device.id != device.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Customer already has an active device"
                ),
            )

        device.status = DeviceStatus.ACTIVE
        device.activation_date = datetime.now(
            timezone.utc
        )

        return self.repository.update(device)

    def update_status(
        self,
        device_id: int,
        data: DeviceStatusUpdate,
    ) -> Device:

        device = self.get_device(device_id)

        new_status = data.status

        if device.status == new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Device is already "
                    f"{new_status.value}"
                ),
            )

        allowed_transitions = {
            DeviceStatus.REGISTERED: {
                DeviceStatus.ACTIVE,
                DeviceStatus.BLOCKED,
                DeviceStatus.DEACTIVATED,
            },
            DeviceStatus.ACTIVE: {
                DeviceStatus.SUSPENDED,
                DeviceStatus.LOST,
                DeviceStatus.BLOCKED,
                DeviceStatus.DEACTIVATED,
            },
            DeviceStatus.SUSPENDED: {
                DeviceStatus.ACTIVE,
                DeviceStatus.BLOCKED,
                DeviceStatus.DEACTIVATED,
            },
            DeviceStatus.LOST: {
                DeviceStatus.BLOCKED,
                DeviceStatus.DEACTIVATED,
            },
            DeviceStatus.BLOCKED: {
                DeviceStatus.DEACTIVATED,
            },
            DeviceStatus.DEACTIVATED: set(),
        }

        if new_status not in allowed_transitions.get(
            device.status,
            set(),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid device status transition: "
                    f"{device.status.value} -> "
                    f"{new_status.value}"
                ),
            )

        if new_status == DeviceStatus.ACTIVE:
            return self.activate_device(device_id)

        device.status = new_status

        return self.repository.update(device)

    def replace_device(
        self,
        device_id: int,
        data: DeviceReplacementCreate,
    ) -> tuple[Device, Device]:

        old_device = self.get_device(device_id)

        if old_device.status not in {
            DeviceStatus.ACTIVE,
            DeviceStatus.LOST,
            DeviceStatus.SUSPENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Active, Lost, or Suspended "
                    "devices can be replaced"
                ),
            )

        new_imei = data.new_imei.strip()

        existing = self.repository.get_by_imei(
            new_imei
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="New IMEI already registered",
            )

        if data.sim_id is not None:
            sim = self.validate_sim(
                data.sim_id
            )

            existing_device = (
                self.repository.get_by_sim_id(
                    data.sim_id
                )
            )

            if existing_device:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "SIM is already assigned "
                        "to another device"
                    ),
                )

            if (
                old_device.customer_id is not None
                and sim.customer_id is not None
                and sim.customer_id
                != old_device.customer_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SIM is assigned to a different customer"
                    ),
                )

        new_device = Device(
            imei=new_imei,
            device_name=data.device_name.strip(),
            manufacturer=data.manufacturer.strip(),
            model_number=data.model_number.strip(),
            device_type=data.device_type,
            status=DeviceStatus.REGISTERED,
            customer_id=old_device.customer_id,
            sim_id=(
                data.sim_id
                if data.sim_id is not None
                else old_device.sim_id
            ),
            replacement_of_device_id=old_device.id,
            replacement_reason=data.reason.strip(),
        )

        old_device.status = DeviceStatus.DEACTIVATED

        self.db.add(old_device)
        self.db.add(new_device)

        self.db.commit()

        self.db.refresh(old_device)
        self.db.refresh(new_device)

        return old_device, new_device

    def search_devices(
        self,
        search: str | None = None,
        device_type=None,
        device_status=None,
        customer_id: int | None = None,
        sim_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ):

        return self.repository.search(
            search=search,
            device_type=device_type,
            device_status=device_status,
            customer_id=customer_id,
            sim_id=sim_id,
            skip=skip,
            limit=limit,
        )