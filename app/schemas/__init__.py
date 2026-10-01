from app.schemas.auth import (
    AccountStatusResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
)

from app.schemas.customer import (
    CustomerAddressCreate,
    CustomerAddressResponse,
    CustomerAddressUpdate,
    CustomerCreate,
    CustomerHistoryResponse,
    CustomerKYCUpdate,
    CustomerResponse,
    CustomerUpdate,
)

from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionStatusUpdate,
    SubscriptionCancellation,
    SubscriptionRenewal,
    SubscriptionResponse,
)

from app.schemas.service_plan import (
    ServicePlanComparisonResponse,
    ServicePlanCreate,
    ServicePlanResponse,
    ServicePlanStatusResponse,
    ServicePlanUpdate,
)

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceStatusUpdate,
    DeviceReplacementCreate,
    DeviceResponse,
    DeviceReplacementResponse,
)

from app.schemas.sim_card import (
    SIMCardCreate,
    SIMCardResponse,
    SIMCardUpdate,
    SIMReplacementCreate,
    SIMReplacementResponse,
    SIMStatusUpdate,
)


from app.schemas.usage import (
    UsageCreate,
    UsageResponse,
    UsageStatusUpdate,
    UsageSummaryResponse,
    UsageUpdate,
)

from app.schemas.network_tower import (
    NetworkTowerCreate,
    NetworkTowerResponse,
    NetworkTowerStatusUpdate,
    NetworkTowerUpdate,
)

from app.schemas.network_outage import (
    OutageCreate,
    OutageUpdate,
    OutageStatusUpdate,
    OutageRestore,
    AffectedCustomersCreate,
    AffectedCustomerResponse,
    OutageResponse,
    OutageListResponse,
    AffectedCustomerListResponse,
    OutageSummaryResponse,
)


from app.schemas.field_technician import (
    FieldTechnicianCreate,
    FieldTechnicianListResponse,
    FieldTechnicianResponse,
    FieldTechnicianUpdate,
    TechnicianAvailabilityUpdate,
    TechnicianStatusUpdate,
)

from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketUpdate,
    TicketStatusUpdate,
    TicketResolution,
    SupportTicketResponse,
    SupportTicketListResponse,
)

from app.schemas.ticket_assignment import (
    TicketAssignmentCreate,
    TicketAssignmentUpdate,
    AssignmentStatusUpdate,
    TicketAssignmentResponse,
    TicketAssignmentListResponse,
)
__all__ = [
    "AccountStatusResponse",
    "LoginRequest",
    "LogoutRequest",
    "PasswordResetConfirm",
    "PasswordResetRequest",
    "RefreshRequest",
    "TokenResponse",
    "UserRegister",
    "UserResponse",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerResponse",
    "CustomerKYCUpdate",
    "CustomerAddressCreate",
    "CustomerAddressUpdate",
    "CustomerAddressResponse",
    "CustomerHistoryResponse",
    "ServicePlanCreate",
    "ServicePlanUpdate",
    "ServicePlanResponse",
    "ServicePlanStatusResponse",
    "ServicePlanComparisonResponse",
    "SIMCardCreate",
    "SIMCardUpdate",
    "SIMCardResponse",
    "SIMStatusUpdate",
    "SIMReplacementCreate",
    "SIMReplacementResponse",
"NetworkTowerCreate",
"NetworkTowerResponse",
"NetworkTowerStatusUpdate",
"NetworkTowerUpdate",
 "FieldTechnicianCreate",
    "FieldTechnicianListResponse",
    "FieldTechnicianResponse",
    "FieldTechnicianUpdate",
    "TechnicianAvailabilityUpdate",
    "TechnicianStatusUpdate",
  "SupportTicketCreate",
    "SupportTicketUpdate",
    "TicketStatusUpdate",
    "TicketResolution",
    "SupportTicketResponse",
    "SupportTicketListResponse",
 "TicketAssignmentCreate",
    "TicketAssignmentUpdate",
    "AssignmentStatusUpdate",
    "TicketAssignmentResponse",
    "TicketAssignmentListResponse",
]