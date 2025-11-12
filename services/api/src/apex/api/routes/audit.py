"""Audit log query endpoints for compliance reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import APIRouter, Depends, Query

from ..audit import query_audit_logs
from ..auth import TokenData, get_current_user
from ..common.helpers import get_code_version, get_model_config
from ..common.models import make_envelope
from ..db import get_db
from ..rbac import require_permission
from ..schemas import ResponseEnvelope

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/logs", response_model=ResponseEnvelope)
@require_permission("audit.read")
async def get_audit_logs(
    user_id: Annotated[str | None, Query(description="Filter by user ID")] = None,
    account_id: Annotated[str | None, Query(description="Filter by account ID")] = None,
    action: Annotated[str | None, Query(description="Filter by action")] = None,
    resource_type: Annotated[str | None, Query(description="Filter by resource type")] = None,
    resource_id: Annotated[str | None, Query(description="Filter by resource ID")] = None,
    start_date: Annotated[datetime | None, Query(description="Start date (ISO format)")] = None,
    end_date: Annotated[datetime | None, Query(description="End date (ISO format)")] = None,
    limit: Annotated[int, Query(ge=1, le=1000, description="Maximum results")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Query audit logs for compliance reporting.

    Requires: audit.read permission

    Retention: 7 years (engineering liability)
    """
    # Non-admins can only view their own account's logs
    if "admin" not in current_user.roles:
        account_id = current_user.account_id

    logs = await query_audit_logs(
        db=db,
        user_id=user_id,
        account_id=account_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return make_envelope(
        result=[
            {
                "log_id": log.log_id,
                "user_id": log.user_id,
                "account_id": log.account_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
                "confidence": log.confidence,
            }
            for log in logs
        ],
        assumptions=[],
        confidence=1.0,
        inputs={
            "user_id": user_id,
            "account_id": account_id,
            "action": action,
        },
        outputs={"count": len(logs)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )

