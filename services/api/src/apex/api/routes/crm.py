"""CRM webhook integration routes."""

from __future__ import annotations

import hashlib
import hmac

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import TokenData, get_current_user_optional
from ..common.models import make_envelope
from ..crm_integration import CRMWebhookPayload, crm_client
from ..db import get_db
from ..deps import get_code_version, get_model_config, settings
from ..schemas import ResponseEnvelope

logger = structlog.get_logger(__name__)


def verify_webhook_signature(
    payload_body: bytes,
    signature_header: str | None,
    secret: str | None,
) -> bool:
    """Verify HMAC-SHA256 webhook signature.

    Args:
        payload_body: Raw request body bytes
        signature_header: Value of X-Webhook-Signature header
        secret: Webhook secret key

    Returns:
        True if signature is valid. In dev mode (ENV != 'production'),
        returns True with warning if secret not configured. In production,
        fails closed if secret is missing.
    """
    # Fail closed in production if no secret configured
    if not secret:
        if settings.ENV == "production":
            logger.error(
                "webhook.signature.missing_secret",
                reason="KEYEDIN_API_KEY not configured in production - rejecting request",
            )
            return False
        # Dev mode: allow bypass with warning
        logger.warning("webhook.signature.skipped", reason="No KEYEDIN_API_KEY configured (dev mode)")
        return True

    if not signature_header:
        logger.warning("webhook.signature.missing")
        return False

    # Compute expected signature
    expected_sig = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Compare signatures (timing-safe)
    is_valid = hmac.compare_digest(f"sha256={expected_sig}", signature_header)

    if not is_valid:
        logger.warning("webhook.signature.invalid")

    return is_valid

router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


class WebhookPayload(BaseModel):
    """Inbound webhook payload from KeyedIn."""
    event_type: str
    project_id: str | None = None
    data: dict


@router.post("/webhooks/keyedin", response_model=ResponseEnvelope)
async def receive_keyedin_webhook(
    payload: WebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
) -> ResponseEnvelope:
    """Receive webhook from KeyedIn CRM.

    Events handled:
    - project.created: Create project in Calcusign
    - project.updated: Update project in Calcusign
    - project.deleted: Soft delete project

    Security: Validates HMAC-SHA256 signature when KEYEDIN_API_KEY is configured.
    """
    # Validate webhook signature
    body = await request.body()
    if not verify_webhook_signature(body, x_webhook_signature, settings.KEYEDIN_API_KEY):
        logger.warning(
            "webhook.rejected",
            event_type=payload.event_type,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    
    # Convert to CRMWebhookPayload
    crm_payload = CRMWebhookPayload(
        event_type=payload.event_type,
        source="keyedin",
        project_id=payload.project_id,
        data=payload.data,
    )
    
    # Handle webhook
    result = await crm_client.handle_inbound_webhook(
        payload=crm_payload,
        db=db,
        user_id="keyedin-system",
        account_id=payload.data.get("account_id", "unknown"),
    )
    
    return make_envelope(
        result=result,
        assumptions=["Webhook received from KeyedIn CRM"],
        confidence=0.95,
        inputs={"event_type": payload.event_type},
        outputs=result,
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.post("/webhooks/send", response_model=ResponseEnvelope)
async def send_webhook_to_keyedin(
    event_type: str,
    data: dict,
    current_user: TokenData | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Send webhook to KeyedIn CRM.
    
    Events sent:
    - calculation.completed: Calculation finished
    - cost.updated: Project cost updated
    - project.submitted: Project submitted for approval
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    success = await crm_client.send_webhook(
        event_type=event_type,
        data=data,
        direction="outbound",
        db=db,
    )
    
    return make_envelope(
        result={"sent": success, "event_type": event_type},
        assumptions=["Webhook sent to KeyedIn CRM"],
        confidence=0.9 if success else 0.5,
        inputs={"event_type": event_type},
        outputs={"sent": success},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )

