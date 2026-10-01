from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.service_plan import ServicePlan
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
)
from app.models.usage import (
    Usage,
    UsageSource,
    UsageStatus,
    UsageType,
)
from app.repositories.usage_repository import (
    UsageRepository,
)
from app.schemas.usage import (
    UsageCreate,
    UsageStatusUpdate,
    UsageSummaryResponse,
    UsageUpdate,
)


class UsageService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsageRepository(db)

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _get_usage_or_404(
        self,
        usage_id: int,
    ) -> Usage:
        usage = self.repository.get_by_id(
            usage_id
        )

        if not usage:
           raise HTTPException(
    status_code=http_status.HTTP_400_BAD_REQUEST,
    detail="Skip cannot be negative",
)

        return usage

    def _get_subscription_or_404(
        self,
        subscription_id: int,
    ) -> Subscription:
        subscription = (
            self.db.query(Subscription)
            .filter(
                Subscription.id
                == subscription_id
            )
            .first()
        )

        if not subscription:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        return subscription

    def _get_customer_or_404(
        self,
        customer_id: int,
    ) -> Customer:
        customer = (
            self.db.query(Customer)
            .filter(
                Customer.id
                == customer_id
            )
            .first()
        )

        if not customer:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        return customer

    def _get_plan_or_404(
        self,
        plan_id: int,
    ) -> ServicePlan:
        plan = (
            self.db.query(ServicePlan)
            .filter(
                ServicePlan.id
                == plan_id
            )
            .first()
        )

        if not plan:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Service plan not found",
            )

        return plan

    def _validate_usage_type_values(
        self,
        payload: UsageCreate,
    ):
        """
        Ensure that the measurement field matches
        the selected usage type.

        Data  -> data_used_mb
        Voice -> voice_minutes
        SMS   -> sms_count
        """

        if payload.usage_type == UsageType.DATA:
            if (
                payload.data_used_mb is None
                or payload.data_used_mb <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Data usage must be greater "
                        "than zero for Data usage"
                    ),
                )

            if (
                payload.voice_minutes is not None
                or payload.sms_count is not None
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Data usage cannot contain "
                        "voice minutes or SMS count"
                    ),
                )

        elif payload.usage_type == UsageType.VOICE:
            if (
                payload.voice_minutes is None
                or payload.voice_minutes <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Voice minutes must be greater "
                        "than zero for Voice usage"
                    ),
                )

            if (
                payload.data_used_mb is not None
                or payload.sms_count is not None
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Voice usage cannot contain "
                        "data usage or SMS count"
                    ),
                )

        elif payload.usage_type == UsageType.SMS:
            if (
                payload.sms_count is None
                or payload.sms_count <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SMS count must be greater "
                        "than zero for SMS usage"
                    ),
                )

            if (
                payload.data_used_mb is not None
                or payload.voice_minutes is not None
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SMS usage cannot contain "
                        "data usage or voice minutes"
                    ),
                )

    def _validate_subscription_customer(
        self,
        subscription: Subscription,
        customer_id: int,
    ):
        if (
            subscription.customer_id
            != customer_id
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Subscription does not belong "
                    "to the specified customer"
                ),
            )

    def _validate_subscription_active(
        self,
        subscription: Subscription,
    ):
        if (
            subscription.status
            != SubscriptionStatus.ACTIVE
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Usage can only be recorded "
                    "for an active subscription"
                ),
            )

    def _validate_usage_date(
        self,
        usage_date: date,
        subscription: Subscription,
    ):
        today = date.today()

        if usage_date > today:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Usage date cannot be in the future",
            )

        if (
            subscription.start_date
            and usage_date
            < subscription.start_date
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Usage date cannot be before "
                    "subscription start date"
                ),
            )

        if (
            subscription.end_date
            and usage_date
            > subscription.end_date
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Usage date cannot be after "
                    "subscription end date"
                ),
            )

    def _get_current_usage_totals(
        self,
        subscription_id: int,
        usage_date: date,
    ):
        """
        Calculate usage within the current
        subscription billing/validity period.
        """

        subscription = self._get_subscription_or_404(
            subscription_id
        )

        start_date = (
            subscription.start_date
            or usage_date
        )

        end_date = (
            subscription.end_date
            or usage_date
        )

        data_used = (
            self.repository.get_total_data_usage(
                subscription_id,
                start_date,
                end_date,
            )
            or Decimal("0")
        )

        voice_used = (
            self.repository.get_total_voice_usage(
                subscription_id,
                start_date,
                end_date,
            )
            or 0
        )

        sms_used = (
            self.repository.get_total_sms_usage(
                subscription_id,
                start_date,
                end_date,
            )
            or 0
        )

        return (
            data_used,
            voice_used,
            sms_used,
        )

    def _validate_plan_allowance(
        self,
        subscription: Subscription,
        usage_type: UsageType,
        data_used_mb: Decimal | None,
        voice_minutes: int | None,
        sms_count: int | None,
        usage_date: date,
    ):
        """
        Prevent usage from exceeding the limits
        configured on the subscription's service plan.

        A NULL plan limit means unlimited usage.
        """

        plan = self._get_plan_or_404(
            subscription.plan_id
        )

        (
            current_data,
            current_voice,
            current_sms,
        ) = self._get_current_usage_totals(
            subscription.id,
            usage_date,
        )

        if usage_type == UsageType.DATA:
            if plan.data_limit_mb is not None:
                new_total = (
                    current_data
                    + Decimal(str(data_used_mb or 0))
                )

                if (
                    new_total
                    > Decimal(
                        str(plan.data_limit_mb)
                    )
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "Data usage exceeds the "
                            "subscription plan limit"
                        ),
                    )

        elif usage_type == UsageType.VOICE:
            if (
                plan.voice_limit_minutes
                is not None
            ):
                new_total = (
                    current_voice
                    + (voice_minutes or 0)
                )

                if (
                    new_total
                    > plan.voice_limit_minutes
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "Voice usage exceeds the "
                            "subscription plan limit"
                        ),
                    )

        elif usage_type == UsageType.SMS:
            if plan.sms_limit is not None:
                new_total = (
                    current_sms
                    + (sms_count or 0)
                )

                if (
                    new_total
                    > plan.sms_limit
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "SMS usage exceeds the "
                            "subscription plan limit"
                        ),
                    )

    # ---------------------------------------------------------
    # Create usage
    # ---------------------------------------------------------

    def create_usage(
        self,
        payload: UsageCreate,
    ) -> Usage:
        """
        Create a usage record after validating:

        - Customer exists
        - Subscription exists
        - Customer/subscription match
        - Subscription is active
        - Usage date is valid
        - Usage type matches measurement
        - Plan allowance is not exceeded
        - Reference ID is not duplicated
        """

        customer = self._get_customer_or_404(
            payload.customer_id
        )

        if not customer.is_active:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Customer is inactive",
            )

        subscription = (
            self._get_subscription_or_404(
                payload.subscription_id
            )
        )

        self._validate_subscription_customer(
            subscription,
            customer.id,
        )

        self._validate_subscription_active(
            subscription
        )

        usage_date = (
            payload.usage_date
            or date.today()
        )

        self._validate_usage_date(
            usage_date,
            subscription,
        )

        self._validate_usage_type_values(
            payload
        )

        if payload.reference_id:
            existing = (
                self.repository
                .get_by_reference_id(
                    payload.reference_id
                )
            )

            if existing:
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=(
                        "Usage reference ID "
                        "already exists"
                    ),
                )

        self._validate_plan_allowance(
            subscription=subscription,
            usage_type=payload.usage_type,
            data_used_mb=payload.data_used_mb,
            voice_minutes=payload.voice_minutes,
            sms_count=payload.sms_count,
            usage_date=usage_date,
        )

        usage = Usage(
            subscription_id=subscription.id,
            customer_id=customer.id,
            usage_type=payload.usage_type,
            usage_date=usage_date,
            data_used_mb=payload.data_used_mb,
            voice_minutes=payload.voice_minutes,
            sms_count=payload.sms_count,
            status=UsageStatus.RECORDED,
            source=payload.source,
            reference_id=payload.reference_id,
            remarks=payload.remarks,
        )

        return self.repository.create(
            usage
        )

    # ---------------------------------------------------------
    # Get usage
    # ---------------------------------------------------------

    def get_usage(
        self,
        usage_id: int,
    ) -> Usage:
        return self._get_usage_or_404(
            usage_id
        )

    # ---------------------------------------------------------
    # Update usage
    # ---------------------------------------------------------

    def update_usage(
        self,
        usage_id: int,
        payload: UsageUpdate,
    ) -> Usage:
        usage = self._get_usage_or_404(
            usage_id
        )

        if (
            usage.status
            != UsageStatus.RECORDED
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Recorded usage can "
                    "be updated"
                ),
            )

        subscription = (
            self._get_subscription_or_404(
                usage.subscription_id
            )
        )

        self._validate_subscription_active(
            subscription
        )

        new_usage_date = (
            payload.usage_date
            if payload.usage_date is not None
            else usage.usage_date
        )

        self._validate_usage_date(
            new_usage_date,
            subscription,
        )

        if (
            payload.reference_id
            and payload.reference_id
            != usage.reference_id
        ):
            existing = (
                self.repository
                .get_by_reference_id(
                    payload.reference_id
                )
            )

            if existing:
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=(
                        "Usage reference ID "
                        "already exists"
                    ),
                )

        # Determine the effective usage values.
        data_used = (
            payload.data_used_mb
            if payload.data_used_mb is not None
            else usage.data_used_mb
        )

        voice_minutes = (
            payload.voice_minutes
            if payload.voice_minutes is not None
            else usage.voice_minutes
        )

        sms_count = (
            payload.sms_count
            if payload.sms_count is not None
            else usage.sms_count
        )

        # Validate values against the existing
        # usage type.
        if (
            usage.usage_type
            == UsageType.DATA
        ):
            if (
                data_used is None
                or data_used <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Data usage must be "
                        "greater than zero"
                    ),
                )

            voice_minutes = None
            sms_count = None

        elif (
            usage.usage_type
            == UsageType.VOICE
        ):
            if (
                voice_minutes is None
                or voice_minutes <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Voice minutes must be "
                        "greater than zero"
                    ),
                )

            data_used = None
            sms_count = None

        elif (
            usage.usage_type
            == UsageType.SMS
        ):
            if (
                sms_count is None
                or sms_count <= 0
            ):
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "SMS count must be "
                        "greater than zero"
                    ),
                )

            data_used = None
            voice_minutes = None

        # Exclude the current record from
        # allowance calculations by temporarily
        # calculating totals and subtracting its
        # existing contribution.
        start_date = (
            subscription.start_date
            or new_usage_date
        )

        end_date = (
            subscription.end_date
            or new_usage_date
        )

        plan = self._get_plan_or_404(
            subscription.plan_id
        )

        current_data = (
            self.repository.get_total_data_usage(
                subscription.id,
                start_date,
                end_date,
            )
            or Decimal("0")
        )

        current_voice = (
            self.repository.get_total_voice_usage(
                subscription.id,
                start_date,
                end_date,
            )
            or 0
        )

        current_sms = (
            self.repository.get_total_sms_usage(
                subscription.id,
                start_date,
                end_date,
            )
            or 0
        )

        if usage.usage_type == UsageType.DATA:
            current_data -= (
                usage.data_used_mb
                or Decimal("0")
            )

            if plan.data_limit_mb is not None:
                if (
                    current_data
                    + Decimal(str(data_used or 0))
                    > Decimal(
                        str(plan.data_limit_mb)
                    )
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "Updated data usage "
                            "exceeds the plan limit"
                        ),
                    )

        elif usage.usage_type == UsageType.VOICE:
            current_voice -= (
                usage.voice_minutes or 0
            )

            if (
                plan.voice_limit_minutes
                is not None
            ):
                if (
                    current_voice
                    + (voice_minutes or 0)
                    > plan.voice_limit_minutes
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "Updated voice usage "
                            "exceeds the plan limit"
                        ),
                    )

        elif usage.usage_type == UsageType.SMS:
            current_sms -= (
                usage.sms_count or 0
            )

            if plan.sms_limit is not None:
                if (
                    current_sms
                    + (sms_count or 0)
                    > plan.sms_limit
                ):
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail=(
                            "Updated SMS usage "
                            "exceeds the plan limit"
                        ),
                    )

        usage.usage_date = new_usage_date
        usage.data_used_mb = data_used
        usage.voice_minutes = voice_minutes
        usage.sms_count = sms_count

        if payload.source is not None:
            usage.source = payload.source

        if payload.reference_id is not None:
            usage.reference_id = (
                payload.reference_id
            )

        if payload.remarks is not None:
            usage.remarks = payload.remarks

        return self.repository.update(
            usage
        )

    # ---------------------------------------------------------
    # Status management
    # ---------------------------------------------------------

    def update_status(
        self,
        usage_id: int,
        payload: UsageStatusUpdate,
    ) -> Usage:
        usage = self._get_usage_or_404(
            usage_id
        )

        current_status = usage.status
        new_status = payload.status

        allowed_transitions = {
            UsageStatus.RECORDED: {
                UsageStatus.PROCESSED,
                UsageStatus.REVERSED,
            },
            UsageStatus.PROCESSED: {
                UsageStatus.REVERSED,
            },
            UsageStatus.REVERSED: set(),
        }

        if (
            new_status
            not in allowed_transitions.get(
                current_status,
                set(),
            )
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid usage status "
                    f"transition: "
                    f"{current_status} -> "
                    f"{new_status}"
                ),
            )

        usage.status = new_status

        return self.repository.update(
            usage
        )

    # ---------------------------------------------------------
    # Process usage
    # ---------------------------------------------------------

    def process_usage(
        self,
        usage_id: int,
    ) -> Usage:
        usage = self._get_usage_or_404(
            usage_id
        )

        if (
            usage.status
            != UsageStatus.RECORDED
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only Recorded usage can "
                    "be processed"
                ),
            )

        usage.status = UsageStatus.PROCESSED

        return self.repository.update(
            usage
        )

    # ---------------------------------------------------------
    # Reverse usage
    # ---------------------------------------------------------

    def reverse_usage(
        self,
        usage_id: int,
        reason: str | None = None,
    ) -> Usage:
        usage = self._get_usage_or_404(
            usage_id
        )

        if (
            usage.status
            == UsageStatus.REVERSED
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Usage is already reversed",
            )

        if reason:
            usage.remarks = (
                f"{usage.remarks or ''} "
                f"Reversal reason: {reason}"
            ).strip()

        usage.status = UsageStatus.REVERSED

        return self.repository.update(
            usage
        )

    # ---------------------------------------------------------
    # Usage summary
    # ---------------------------------------------------------

    def get_usage_summary(
        self,
        subscription_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> UsageSummaryResponse:
        subscription = (
            self._get_subscription_or_404(
                subscription_id
            )
        )

        if start_date is None:
            start_date = (
                subscription.start_date
                or date.today()
            )

        if end_date is None:
            end_date = (
                subscription.end_date
                or date.today()
            )

        if start_date > end_date:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Start date cannot be "
                    "after end date"
                ),
            )

        plan = self._get_plan_or_404(
            subscription.plan_id
        )

        summary = (
            self.repository.get_usage_summary(
                subscription_id,
                start_date,
                end_date,
            )
        )

        total_data = (
            summary["total_data_used_mb"]
            or Decimal("0")
        )

        total_voice = (
            summary["total_voice_minutes"]
            or 0
        )

        total_sms = (
            summary["total_sms_count"]
            or 0
        )

        remaining_data = None
        remaining_voice = None
        remaining_sms = None

        if plan.data_limit_mb is not None:
            remaining_data = max(
                Decimal(
                    str(plan.data_limit_mb)
                )
                - total_data,
                Decimal("0"),
            )

        if (
            plan.voice_limit_minutes
            is not None
        ):
            remaining_voice = max(
                plan.voice_limit_minutes
                - total_voice,
                0,
            )

        if plan.sms_limit is not None:
            remaining_sms = max(
                plan.sms_limit
                - total_sms,
                0,
            )

        return UsageSummaryResponse(
            customer_id=subscription.customer_id,
            subscription_id=subscription.id,
            period_start=start_date,
            period_end=end_date,
            total_data_used_mb=total_data,
            total_voice_minutes=total_voice,
            total_sms_count=total_sms,
            data_limit_mb=plan.data_limit_mb,
            voice_limit_minutes=(
                plan.voice_limit_minutes
            ),
            sms_limit=plan.sms_limit,
            remaining_data_mb=remaining_data,
            remaining_voice_minutes=remaining_voice,
            remaining_sms=remaining_sms,
        )

    # ---------------------------------------------------------
    # Usage history
    # ---------------------------------------------------------

    def search_usage(
        self,
        customer_id: int | None = None,
        subscription_id: int | None = None,
        usage_type: UsageType | None = None,
        status: UsageStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ):
        if skip < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Skip cannot be negative",
            )

        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Limit must be between "
                    "1 and 100"
                ),
            )

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Start date cannot be "
                    "after end date"
                ),
            )

        if customer_id is not None:
            self._get_customer_or_404(
                customer_id
            )

        if subscription_id is not None:
            subscription = (
                self._get_subscription_or_404(
                    subscription_id
                )
            )

            if (
                customer_id is not None
                and subscription.customer_id
                != customer_id
            ):
                raise HTTPException(
                    status_code=(
                        http_status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Subscription does not "
                        "belong to the specified "
                        "customer"
                    ),
                )

        records = self.repository.search(
            customer_id=customer_id,
            subscription_id=subscription_id,
            usage_type=usage_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            search=search,
            skip=skip,
            limit=limit,
        )

        total = self.repository.count(
            customer_id=customer_id,
            subscription_id=subscription_id,
            usage_type=usage_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "items": records,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
