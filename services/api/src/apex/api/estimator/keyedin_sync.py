"""KeyedIn integration for estimator pricing sync.

This module handles bidirectional sync between SignX estimates and KeyedIn CRM:
- Pull material pricing from KeyedIn catalog
- Push quotes to KeyedIn as opportunities
- Sync estimate status with KeyedIn pipeline

TODO: Implement actual KeyedIn API integration when credentials are available.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
import structlog
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import settings

logger = structlog.get_logger(__name__)


# ============================================================
# KeyedIn API Models
# ============================================================

class KeyedInPriceUpdate(BaseModel):
    """Price update from KeyedIn."""
    part_number: str
    unit_cost: Decimal
    effective_date: datetime
    vendor: str | None = None


class KeyedInQuote(BaseModel):
    """Quote to push to KeyedIn."""
    estimate_number: str
    customer_name: str
    project_name: str
    quoted_price: Decimal
    gross_margin_percent: Decimal
    status: str
    valid_until: datetime | None = None
    line_items: list[dict] = []


class KeyedInSyncResult(BaseModel):
    """Result of sync operation."""
    success: bool
    keyedin_id: str | None = None
    message: str
    synced_at: datetime | None = None


# ============================================================
# KeyedIn Client
# ============================================================

class KeyedInEstimatorClient:
    """Client for KeyedIn estimator integrations.

    Handles:
    - Material pricing sync from KeyedIn catalog
    - Quote push to KeyedIn opportunities
    - Estimate status sync with KeyedIn pipeline
    """

    def __init__(self):
        self.api_url = getattr(settings, "KEYEDIN_API_URL", None)
        self.api_key = getattr(settings, "KEYEDIN_API_KEY", None)
        self.timeout = 30.0
        self._enabled = bool(self.api_url and self.api_key)

    @property
    def is_enabled(self) -> bool:
        """Check if KeyedIn integration is configured."""
        return self._enabled

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
    ) -> dict | None:
        """Make authenticated request to KeyedIn API."""
        if not self._enabled:
            logger.debug("keyedin.not_configured", endpoint=endpoint)
            return None

        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SignX-Estimator/1.0",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if response.status_code >= 400:
                    logger.error(
                        "keyedin.request_failed",
                        endpoint=endpoint,
                        status=response.status_code,
                        body=response.text[:200],
                    )
                    return None

                return response.json()

        except Exception as e:
            logger.error("keyedin.request_error", endpoint=endpoint, error=str(e))
            return None

    # ============================================================
    # Material Pricing
    # ============================================================

    async def fetch_material_price(
        self,
        part_number: str,
    ) -> KeyedInPriceUpdate | None:
        """Fetch current price for a material from KeyedIn.

        Args:
            part_number: Material part number

        Returns:
            Price update or None if not found/not configured
        """
        logger.info("keyedin.fetch_price", part_number=part_number)

        if not self._enabled:
            # Return None - caller should use local catalog
            return None

        # TODO: Implement actual KeyedIn API call
        # endpoint = f"materials/{part_number}/price"
        # result = await self._request("GET", endpoint)
        # if result:
        #     return KeyedInPriceUpdate(**result)

        logger.debug("keyedin.price_stub", part_number=part_number, message="Using local catalog")
        return None

    async def sync_material_catalog(
        self,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Sync material catalog prices from KeyedIn.

        TODO: Implement bulk price sync from KeyedIn catalog API.

        Returns:
            Sync result with counts
        """
        logger.info("keyedin.sync_catalog_start")

        if not self._enabled:
            return {
                "success": False,
                "message": "KeyedIn integration not configured",
                "updated": 0,
                "errors": 0,
            }

        # TODO: Implement bulk sync
        # 1. Fetch all prices from KeyedIn: GET /catalog/prices
        # 2. Update local MaterialCatalog records
        # 3. Track last_cost_update and keyedin_price_date

        return {
            "success": True,
            "message": "Catalog sync not yet implemented",
            "updated": 0,
            "errors": 0,
            "synced_at": datetime.now(UTC).isoformat(),
        }

    # ============================================================
    # Quote Sync
    # ============================================================

    async def push_quote_to_keyedin(
        self,
        estimate_id: UUID,
        db: AsyncSession,
    ) -> KeyedInSyncResult:
        """Push estimate as quote to KeyedIn CRM.

        Creates or updates an opportunity in KeyedIn with:
        - Customer info
        - Quote amount
        - Line item summary
        - Status mapping

        Args:
            estimate_id: Estimate UUID
            db: Database session

        Returns:
            Sync result
        """
        from .models import Estimate

        logger.info("keyedin.push_quote", estimate_id=str(estimate_id))

        # Fetch estimate with items
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Estimate)
            .where(Estimate.id == estimate_id)
            .options(
                selectinload(Estimate.labor_items),
                selectinload(Estimate.material_items),
            )
        )
        estimate = result.scalar_one_or_none()

        if not estimate:
            return KeyedInSyncResult(
                success=False,
                message=f"Estimate {estimate_id} not found",
            )

        if not self._enabled:
            return KeyedInSyncResult(
                success=False,
                message="KeyedIn integration not configured - quote not synced",
            )

        # Build quote payload
        quote = KeyedInQuote(
            estimate_number=estimate.estimate_number,
            customer_name=estimate.customer_name,
            project_name=estimate.project_name,
            quoted_price=estimate.quoted_price,
            gross_margin_percent=estimate.gross_margin_percent,
            status=estimate.status.value,
            valid_until=estimate.valid_until,
            line_items=[
                {"type": "labor", "count": len(estimate.labor_items), "total": str(estimate.labor_total)},
                {"type": "materials", "count": len(estimate.material_items), "total": str(estimate.materials_total)},
            ],
        )

        # TODO: Implement actual KeyedIn API call
        # endpoint = "opportunities"
        # if estimate.keyedin_quote_id:
        #     endpoint = f"opportunities/{estimate.keyedin_quote_id}"
        #     result = await self._request("PUT", endpoint, quote.model_dump())
        # else:
        #     result = await self._request("POST", endpoint, quote.model_dump())
        #
        # if result:
        #     estimate.keyedin_quote_id = result.get("id")
        #     estimate.keyedin_synced_at = datetime.now(UTC)
        #     await db.commit()
        #     return KeyedInSyncResult(success=True, keyedin_id=result.get("id"))

        logger.debug(
            "keyedin.quote_stub",
            estimate_number=estimate.estimate_number,
            message="KeyedIn push not yet implemented",
        )

        return KeyedInSyncResult(
            success=True,
            message="Quote push not yet implemented - will sync when KeyedIn API is connected",
            synced_at=datetime.now(UTC),
        )

    async def pull_quote_status(
        self,
        estimate_id: UUID,
        db: AsyncSession,
    ) -> KeyedInSyncResult:
        """Pull quote status from KeyedIn.

        Updates local estimate status based on KeyedIn opportunity stage.

        Args:
            estimate_id: Estimate UUID
            db: Database session

        Returns:
            Sync result
        """
        from .models import Estimate

        logger.info("keyedin.pull_status", estimate_id=str(estimate_id))

        result = await db.execute(
            select(Estimate).where(Estimate.id == estimate_id)
        )
        estimate = result.scalar_one_or_none()

        if not estimate:
            return KeyedInSyncResult(
                success=False,
                message=f"Estimate {estimate_id} not found",
            )

        if not estimate.keyedin_quote_id:
            return KeyedInSyncResult(
                success=False,
                message="Estimate not linked to KeyedIn quote",
            )

        if not self._enabled:
            return KeyedInSyncResult(
                success=False,
                message="KeyedIn integration not configured",
            )

        # TODO: Implement actual KeyedIn API call
        # endpoint = f"opportunities/{estimate.keyedin_quote_id}"
        # result = await self._request("GET", endpoint)
        # if result:
        #     keyedin_status = result.get("stage")
        #     # Map KeyedIn stage to EstimateStatus
        #     status_map = {
        #         "prospect": EstimateStatus.DRAFT,
        #         "proposal": EstimateStatus.SENT,
        #         "negotiation": EstimateStatus.PENDING,
        #         "closed_won": EstimateStatus.ACCEPTED,
        #         "closed_lost": EstimateStatus.REJECTED,
        #     }
        #     new_status = status_map.get(keyedin_status)
        #     if new_status and new_status != estimate.status:
        #         estimate.status = new_status
        #         estimate.keyedin_synced_at = datetime.now(UTC)
        #         await db.commit()

        return KeyedInSyncResult(
            success=True,
            message="Status pull not yet implemented",
            synced_at=datetime.now(UTC),
        )

    # ============================================================
    # Webhook Handlers
    # ============================================================

    async def handle_price_update_webhook(
        self,
        payload: dict,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Handle price update webhook from KeyedIn.

        Updates local MaterialCatalog with new pricing.

        Args:
            payload: Webhook payload with price updates
            db: Database session

        Returns:
            Processing result
        """
        from .models import MaterialCatalog

        logger.info("keyedin.price_update_webhook", item_count=len(payload.get("items", [])))

        updated = 0
        errors = 0

        for item in payload.get("items", []):
            try:
                part_number = item.get("part_number")
                new_price = Decimal(str(item.get("unit_cost", 0)))

                result = await db.execute(
                    select(MaterialCatalog).where(MaterialCatalog.part_number == part_number)
                )
                material = result.scalar_one_or_none()

                if material:
                    material.unit_cost = new_price
                    material.last_cost_update = datetime.now(UTC)
                    material.keyedin_price_date = datetime.fromisoformat(item.get("effective_date")) if item.get("effective_date") else None
                    updated += 1
                else:
                    logger.warning("keyedin.material_not_found", part_number=part_number)
                    errors += 1

            except Exception as e:
                logger.error("keyedin.price_update_error", error=str(e))
                errors += 1

        await db.commit()

        return {
            "processed": len(payload.get("items", [])),
            "updated": updated,
            "errors": errors,
        }

    async def handle_quote_status_webhook(
        self,
        payload: dict,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Handle quote status change webhook from KeyedIn.

        Updates local estimate status based on KeyedIn opportunity changes.

        Args:
            payload: Webhook payload with status change
            db: Database session

        Returns:
            Processing result
        """
        from .models import Estimate, EstimateStatus

        keyedin_id = payload.get("opportunity_id")
        new_stage = payload.get("stage")

        logger.info("keyedin.status_webhook", keyedin_id=keyedin_id, stage=new_stage)

        # Find estimate by KeyedIn ID
        result = await db.execute(
            select(Estimate).where(Estimate.keyedin_quote_id == keyedin_id)
        )
        estimate = result.scalar_one_or_none()

        if not estimate:
            return {"status": "not_found", "keyedin_id": keyedin_id}

        # Map KeyedIn stage to EstimateStatus
        status_map = {
            "prospect": EstimateStatus.DRAFT,
            "proposal": EstimateStatus.SENT,
            "negotiation": EstimateStatus.PENDING,
            "closed_won": EstimateStatus.ACCEPTED,
            "closed_lost": EstimateStatus.REJECTED,
        }

        new_status = status_map.get(new_stage)
        if new_status and new_status != estimate.status:
            old_status = estimate.status
            estimate.status = new_status
            estimate.keyedin_synced_at = datetime.now(UTC)
            await db.commit()

            logger.info(
                "keyedin.status_updated",
                estimate_number=estimate.estimate_number,
                old_status=old_status.value,
                new_status=new_status.value,
            )

            return {
                "status": "updated",
                "estimate_number": estimate.estimate_number,
                "old_status": old_status.value,
                "new_status": new_status.value,
            }

        return {"status": "no_change", "estimate_number": estimate.estimate_number}


# Global client instance
keyedin_estimator = KeyedInEstimatorClient()
