from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


INDEX_STATEMENTS = {
    "ix_audit_logs_user_created": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_audit_logs_user_created "
        "ON audit_logs (user_id, created_at)"
    ),
    "ix_audit_logs_resource_created": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_audit_logs_resource_created "
        "ON audit_logs (resource, created_at)"
    ),
    "ix_audit_logs_action_created": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_audit_logs_action_created "
        "ON audit_logs (action, created_at)"
    ),
    "ix_usage_customer_date": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_usage_customer_date "
        "ON usage_records (customer_id, usage_date)"
    ),
    "ix_usage_subscription_date": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_usage_subscription_date "
        "ON usage_records (subscription_id, usage_date)"
    ),
    "ix_outage_tower_start": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_outage_tower_start "
        "ON network_outages (tower_id, start_time)"
    ),
    "ix_ticket_customer_status": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_ticket_customer_status "
        "ON support_tickets (customer_id, status)"
    ),
    "ix_ticket_status_created": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_ticket_status_created "
        "ON support_tickets (status, created_at)"
    ),
    "ix_assignment_user_status": (
        "CREATE INDEX IF NOT EXISTS "
        "ix_assignment_user_status "
        "ON ticket_assignments "
        "(assigned_user_id, status)"
    ),
}


def create_performance_indexes(
    engine: Engine,
):
    """
    Create additional composite indexes used by
    reporting, audit, support, usage and operations queries.

    CREATE INDEX IF NOT EXISTS keeps this safe to call
    repeatedly during application startup.
    """

    inspector = inspect(engine)

    existing_indexes = {}

    for table_name in (
        "audit_logs",
        "usage_records",
        "network_outages",
        "support_tickets",
        "ticket_assignments",
    ):
        try:
            existing_indexes[table_name] = {
                index["name"]
                for index in inspector.get_indexes(
                    table_name
                )
            }
        except Exception:
            existing_indexes[table_name] = set()

    with engine.begin() as connection:

        for index_name, statement in INDEX_STATEMENTS.items():

            table_name = index_name.split(
                "_",
                3,
            )[2] if False else None

            # SQLite and PostgreSQL both support
            # CREATE INDEX IF NOT EXISTS.
            connection.execute(
                text(statement)
            )