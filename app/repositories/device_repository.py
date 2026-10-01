from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.device import (
    Device,
    DeviceStatus,
    DeviceType,
)


class DeviceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(
        self,
        device_id: int,
    ) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.id == device_id
            )
        )

    def get_by_imei(
        self,
        imei: str,
    ) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.imei == imei
            )
        )

    def get_by_sim_id(
        self,
        sim_id: int,
    ) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.sim_id == sim_id
            )
        )

    def get_active_customer_device(
        self,
        customer_id: int,
    ) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.customer_id == customer_id,
                Device.status == DeviceStatus.ACTIVE,
            )
        )

    def create(
        self,
        device: Device,
    ) -> Device:
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)

        return device

    def update(
        self,
        device: Device,
    ) -> Device:
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)

        return device

    def search(
        self,
        search: str | None = None,
        device_type: DeviceType | None = None,
        device_status: DeviceStatus | None = None,
        customer_id: int | None = None,
        sim_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Device], int]:

        query = select(Device)

        if search:
            pattern = f"%{search}%"

            query = query.where(
                or_(
                    Device.imei.ilike(pattern),
                    Device.device_name.ilike(pattern),
                    Device.manufacturer.ilike(pattern),
                    Device.model_number.ilike(pattern),
                )
            )

        if device_type is not None:
            query = query.where(
                Device.device_type == device_type
            )

        if device_status is not None:
            query = query.where(
                Device.status == device_status
            )

        if customer_id is not None:
            query = query.where(
                Device.customer_id == customer_id
            )

        if sim_id is not None:
            query = query.where(
                Device.sim_id == sim_id
            )

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        total = self.db.scalar(
            count_query
        ) or 0

        devices = list(
            self.db.scalars(
                query
                .order_by(Device.id.desc())
                .offset(skip)
                .limit(limit)
            )
        )

        return devices, total