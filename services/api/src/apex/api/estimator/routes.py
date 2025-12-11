"""Estimator API routes for quotes, BOM, and labor takeoff."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import TokenData, get_current_user_optional
from ..common.models import make_envelope
from ..db import get_db
from ..deps import get_code_version, get_model_config, settings
from ..schemas import ResponseEnvelope

from .models import (
    Estimate,
    EstimateStatus,
    LaborCategory,
    LaborLineItem,
    MaterialCategory,
    MaterialCatalog,
    MaterialLineItem,
    PermitItem,
    SubcontractorItem,
    WorkCode,
)
from .schemas import (
    AISuggestionRequest,
    AISuggestionResponse,
    EstimateCreate,
    EstimateResponse,
    EstimateSummary,
    EstimateUpdate,
    LaborLineCreate,
    LaborLineResponse,
    LaborLineUpdate,
    MaterialCatalogResponse,
    MaterialCatalogSearch,
    MaterialLineCreate,
    MaterialLineResponse,
    MaterialLineUpdate,
    PermitItemCreate,
    PermitItemResponse,
    SubcontractorItemCreate,
    SubcontractorItemResponse,
    WorkCodeResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/estimates", tags=["estimator"])


# ============================================================
# Helper Functions
# ============================================================

def _generate_estimate_number() -> str:
    """Generate estimate number: EST-YYYYMMDD-XXXX."""
    today = datetime.now(UTC).strftime("%Y%m%d")
    random_suffix = uuid4().hex[:4].upper()
    return f"EST-{today}-{random_suffix}"


def _recalculate_estimate(estimate: Estimate) -> None:
    """Recalculate all estimate totals from line items."""
    # Labor totals
    estimate.labor_hours = sum(
        item.hours for item in estimate.labor_items
    ) or Decimal("0")
    estimate.labor_subtotal = sum(
        item.extended for item in estimate.labor_items
    ) or Decimal("0")
    estimate.labor_burden_amount = (
        estimate.labor_subtotal * estimate.labor_burden_percent / 100
    )
    estimate.labor_total = estimate.labor_subtotal + estimate.labor_burden_amount

    # Materials totals
    estimate.materials_subtotal = sum(
        item.extended for item in estimate.material_items
    ) or Decimal("0")
    taxable_materials = sum(
        item.extended for item in estimate.material_items if item.is_taxable
    ) or Decimal("0")
    estimate.materials_tax_amount = (
        taxable_materials * estimate.materials_tax_percent / 100
    )
    estimate.materials_total = (
        estimate.materials_subtotal
        + estimate.materials_tax_amount
        + estimate.materials_freight
    )

    # Subcontractors and permits
    estimate.subcontractors_total = sum(
        item.amount for item in estimate.subcontractor_items
    ) or Decimal("0")
    estimate.permits_total = sum(
        item.amount for item in estimate.permit_items
    ) or Decimal("0")

    # Roll-up totals
    estimate.direct_cost = (
        estimate.labor_total
        + estimate.materials_total
        + estimate.subcontractors_total
        + estimate.permits_total
    )
    estimate.overhead_amount = estimate.direct_cost * estimate.overhead_percent / 100
    estimate.profit_amount = (
        (estimate.direct_cost + estimate.overhead_amount)
        * estimate.profit_percent
        / 100
    )
    estimate.sell_price = (
        estimate.direct_cost + estimate.overhead_amount + estimate.profit_amount
    )

    # If no manual override, quoted price = sell price
    if estimate.quoted_price == Decimal("0"):
        estimate.quoted_price = estimate.sell_price

    # Gross margin
    if estimate.quoted_price > 0:
        estimate.gross_margin_percent = (
            (estimate.quoted_price - estimate.direct_cost)
            / estimate.quoted_price
            * 100
        )
    else:
        estimate.gross_margin_percent = Decimal("0")

    # Update valid_until
    if estimate.valid_days:
        from datetime import timedelta
        estimate.valid_until = datetime.now(UTC) + timedelta(days=estimate.valid_days)


async def _get_estimate_with_items(
    estimate_id: UUID, db: AsyncSession
) -> Estimate:
    """Fetch estimate with all line items eagerly loaded."""
    result = await db.execute(
        select(Estimate)
        .where(Estimate.id == estimate_id)
        .options(
            selectinload(Estimate.labor_items),
            selectinload(Estimate.material_items),
            selectinload(Estimate.subcontractor_items),
            selectinload(Estimate.permit_items),
        )
    )
    estimate = result.scalar_one_or_none()
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estimate {estimate_id} not found",
        )
    return estimate


# ============================================================
# Estimate CRUD
# ============================================================

@router.get("/", response_model=ResponseEnvelope)
async def list_estimates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: EstimateStatus | None = Query(None, alias="status"),
    customer: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> ResponseEnvelope:
    """List estimates with optional filters."""
    logger.info(
        "estimates.list",
        skip=skip,
        limit=limit,
        status=status_filter,
        customer=customer,
    )

    query = select(Estimate).order_by(Estimate.created_at.desc())

    if status_filter:
        query = query.where(Estimate.status == status_filter)
    if customer:
        query = query.where(Estimate.customer_name.ilike(f"%{customer}%"))

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    estimates = result.scalars().all()

    # Get total count
    count_query = select(func.count(Estimate.id))
    if status_filter:
        count_query = count_query.where(Estimate.status == status_filter)
    if customer:
        count_query = count_query.where(Estimate.customer_name.ilike(f"%{customer}%"))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    summaries = [
        EstimateSummary.model_validate(est).model_dump() for est in estimates
    ]

    return make_envelope(
        result={"estimates": summaries, "total": total, "skip": skip, "limit": limit},
        assumptions=["Results sorted by created_at descending"],
        confidence=0.95,
        inputs={"skip": skip, "limit": limit, "status": status_filter, "customer": customer},
        outputs={"count": len(summaries), "total": total},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.post("/", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
async def create_estimate(
    req: EstimateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> ResponseEnvelope:
    """Create a new estimate."""
    created_by = current_user.user_id if current_user else "anonymous"
    logger.info("estimates.create", customer=req.customer_name, created_by=created_by)

    estimate = Estimate(
        id=uuid4(),
        estimate_number=_generate_estimate_number(),
        project_id=req.project_id,
        status=EstimateStatus.DRAFT,
        created_by=created_by,
        # Customer
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        customer_phone=req.customer_phone,
        customer_company=req.customer_company,
        # Project
        project_name=req.project_name,
        job_site_address=req.job_site_address,
        city=req.city,
        state=req.state,
        zip_code=req.zip_code,
        # Sign specs (JSON)
        sign_specs=req.sign_specs.model_dump() if req.sign_specs else None,
        # Engineering
        wind_speed_mph=req.wind_speed_mph,
        exposure_category=req.exposure_category,
        # Markup percentages
        labor_burden_percent=req.labor_burden_percent,
        materials_tax_percent=req.materials_tax_percent,
        materials_freight=req.materials_freight,
        overhead_percent=req.overhead_percent,
        profit_percent=req.profit_percent,
        # Notes
        internal_notes=req.internal_notes,
        customer_notes=req.customer_notes,
        terms_conditions=req.terms_conditions,
        # Validity
        valid_days=req.valid_days,
        lead_time_days=req.lead_time_days,
    )

    # Initialize totals
    _recalculate_estimate(estimate)

    db.add(estimate)
    await db.commit()
    await db.refresh(estimate)

    return make_envelope(
        result={
            "id": str(estimate.id),
            "estimate_number": estimate.estimate_number,
            "status": estimate.status.value,
        },
        assumptions=["Estimate created in DRAFT status", "Totals initialized to zero"],
        confidence=0.95,
        inputs=req.model_dump(),
        outputs={"estimate_number": estimate.estimate_number},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.get("/{estimate_id}", response_model=ResponseEnvelope)
async def get_estimate(
    estimate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Get estimate with all line items."""
    logger.info("estimates.get", estimate_id=str(estimate_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    response = EstimateResponse.model_validate(estimate)

    return make_envelope(
        result=response.model_dump(),
        assumptions=[],
        confidence=0.95,
        inputs={"estimate_id": str(estimate_id)},
        outputs={"status": estimate.status.value},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.put("/{estimate_id}", response_model=ResponseEnvelope)
async def update_estimate(
    estimate_id: UUID,
    req: EstimateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> ResponseEnvelope:
    """Update estimate fields."""
    logger.info("estimates.update", estimate_id=str(estimate_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    # Check if estimate can be modified
    if estimate.status in (EstimateStatus.ACCEPTED, EstimateStatus.INVOICED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot modify estimate in {estimate.status.value} status",
        )

    # Update fields if provided
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "sign_specs" and value:
            setattr(estimate, field, value.model_dump() if hasattr(value, "model_dump") else value)
        elif hasattr(estimate, field):
            setattr(estimate, field, value)

    estimate.updated_at = datetime.now(UTC)
    _recalculate_estimate(estimate)

    await db.commit()
    await db.refresh(estimate)

    return make_envelope(
        result={"id": str(estimate.id), "status": estimate.status.value, "updated": True},
        assumptions=["Totals recalculated after update"],
        confidence=0.95,
        inputs={"estimate_id": str(estimate_id), "updates": list(update_data.keys())},
        outputs={"quoted_price": str(estimate.quoted_price)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.delete("/{estimate_id}", response_model=ResponseEnvelope)
async def delete_estimate(
    estimate_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData | None = Depends(get_current_user_optional),
) -> ResponseEnvelope:
    """Delete estimate (soft delete by setting status to CANCELLED)."""
    logger.info("estimates.delete", estimate_id=str(estimate_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    if estimate.status in (EstimateStatus.ACCEPTED, EstimateStatus.INVOICED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete estimate in {estimate.status.value} status",
        )

    estimate.status = EstimateStatus.CANCELLED
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={"id": str(estimate.id), "status": "cancelled", "deleted": True},
        assumptions=["Soft delete - status set to CANCELLED"],
        confidence=0.95,
        inputs={"estimate_id": str(estimate_id)},
        outputs={"status": "cancelled"},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Labor Line Items
# ============================================================

@router.post("/{estimate_id}/labor", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
async def add_labor_item(
    estimate_id: UUID,
    req: LaborLineCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Add labor line item to estimate."""
    logger.info("estimates.labor.add", estimate_id=str(estimate_id), work_code=req.work_code)

    estimate = await _get_estimate_with_items(estimate_id, db)

    if estimate.status not in (EstimateStatus.DRAFT, EstimateStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot add items to estimate in {estimate.status.value} status",
        )

    labor_item = LaborLineItem(
        id=uuid4(),
        estimate_id=estimate_id,
        work_code=req.work_code,
        description=req.description,
        category=req.category,
        hours=req.hours,
        rate=req.rate,
        extended=req.hours * req.rate,
        notes=req.notes,
        sort_order=req.sort_order,
    )

    db.add(labor_item)
    estimate.labor_items.append(labor_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(labor_item)

    response = LaborLineResponse.model_validate(labor_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Extended = hours * rate", "Estimate totals recalculated"],
        confidence=0.95,
        inputs=req.model_dump(),
        outputs={"labor_total": str(estimate.labor_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.put("/{estimate_id}/labor/{item_id}", response_model=ResponseEnvelope)
async def update_labor_item(
    estimate_id: UUID,
    item_id: UUID,
    req: LaborLineUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Update labor line item."""
    logger.info("estimates.labor.update", estimate_id=str(estimate_id), item_id=str(item_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    labor_item = next((i for i in estimate.labor_items if i.id == item_id), None)
    if not labor_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Labor item {item_id} not found",
        )

    # Update fields
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(labor_item, field):
            setattr(labor_item, field, value)

    # Recalculate extended
    labor_item.extended = labor_item.hours * labor_item.rate
    labor_item.updated_at = datetime.now(UTC)

    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    response = LaborLineResponse.model_validate(labor_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Extended recalculated", "Estimate totals recalculated"],
        confidence=0.95,
        inputs=update_data,
        outputs={"extended": str(labor_item.extended)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.delete("/{estimate_id}/labor/{item_id}", response_model=ResponseEnvelope)
async def delete_labor_item(
    estimate_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Delete labor line item."""
    logger.info("estimates.labor.delete", estimate_id=str(estimate_id), item_id=str(item_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    labor_item = next((i for i in estimate.labor_items if i.id == item_id), None)
    if not labor_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Labor item {item_id} not found",
        )

    await db.delete(labor_item)
    estimate.labor_items.remove(labor_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={"deleted": True, "item_id": str(item_id)},
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs={"item_id": str(item_id)},
        outputs={"labor_total": str(estimate.labor_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Material Line Items
# ============================================================

@router.post("/{estimate_id}/materials", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
async def add_material_item(
    estimate_id: UUID,
    req: MaterialLineCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Add material line item to estimate."""
    logger.info("estimates.material.add", estimate_id=str(estimate_id), part_number=req.part_number)

    estimate = await _get_estimate_with_items(estimate_id, db)

    if estimate.status not in (EstimateStatus.DRAFT, EstimateStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot add items to estimate in {estimate.status.value} status",
        )

    material_item = MaterialLineItem(
        id=uuid4(),
        estimate_id=estimate_id,
        part_number=req.part_number,
        description=req.description,
        category=req.category,
        quantity=req.quantity,
        unit=req.unit,
        unit_cost=req.unit_cost,
        extended=req.quantity * req.unit_cost,
        vendor=req.vendor,
        vendor_part_number=req.vendor_part_number,
        lead_time_days=req.lead_time_days,
        notes=req.notes,
        sort_order=req.sort_order,
        is_taxable=req.is_taxable,
    )

    db.add(material_item)
    estimate.material_items.append(material_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(material_item)

    response = MaterialLineResponse.model_validate(material_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Extended = quantity * unit_cost", "Estimate totals recalculated"],
        confidence=0.95,
        inputs=req.model_dump(),
        outputs={"materials_total": str(estimate.materials_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.put("/{estimate_id}/materials/{item_id}", response_model=ResponseEnvelope)
async def update_material_item(
    estimate_id: UUID,
    item_id: UUID,
    req: MaterialLineUpdate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Update material line item."""
    logger.info("estimates.material.update", estimate_id=str(estimate_id), item_id=str(item_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    material_item = next((i for i in estimate.material_items if i.id == item_id), None)
    if not material_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material item {item_id} not found",
        )

    # Update fields
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(material_item, field):
            setattr(material_item, field, value)

    # Recalculate extended
    material_item.extended = material_item.quantity * material_item.unit_cost
    material_item.updated_at = datetime.now(UTC)

    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    response = MaterialLineResponse.model_validate(material_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Extended recalculated", "Estimate totals recalculated"],
        confidence=0.95,
        inputs=update_data,
        outputs={"extended": str(material_item.extended)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.delete("/{estimate_id}/materials/{item_id}", response_model=ResponseEnvelope)
async def delete_material_item(
    estimate_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Delete material line item."""
    logger.info("estimates.material.delete", estimate_id=str(estimate_id), item_id=str(item_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    material_item = next((i for i in estimate.material_items if i.id == item_id), None)
    if not material_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material item {item_id} not found",
        )

    await db.delete(material_item)
    estimate.material_items.remove(material_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={"deleted": True, "item_id": str(item_id)},
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs={"item_id": str(item_id)},
        outputs={"materials_total": str(estimate.materials_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Subcontractor Items
# ============================================================

@router.post("/{estimate_id}/subcontractors", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
async def add_subcontractor_item(
    estimate_id: UUID,
    req: SubcontractorItemCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Add subcontractor item to estimate."""
    logger.info("estimates.subcontractor.add", estimate_id=str(estimate_id), vendor=req.vendor_name)

    estimate = await _get_estimate_with_items(estimate_id, db)

    sub_item = SubcontractorItem(
        id=uuid4(),
        estimate_id=estimate_id,
        vendor_name=req.vendor_name,
        description=req.description,
        trade=req.trade,
        amount=req.amount,
        quote_number=req.quote_number,
        quote_date=req.quote_date,
        notes=req.notes,
        sort_order=req.sort_order,
    )

    db.add(sub_item)
    estimate.subcontractor_items.append(sub_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(sub_item)

    response = SubcontractorItemResponse.model_validate(sub_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs=req.model_dump(),
        outputs={"subcontractors_total": str(estimate.subcontractors_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.delete("/{estimate_id}/subcontractors/{item_id}", response_model=ResponseEnvelope)
async def delete_subcontractor_item(
    estimate_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Delete subcontractor item."""
    estimate = await _get_estimate_with_items(estimate_id, db)

    sub_item = next((i for i in estimate.subcontractor_items if i.id == item_id), None)
    if not sub_item:
        raise HTTPException(status_code=404, detail=f"Subcontractor item {item_id} not found")

    await db.delete(sub_item)
    estimate.subcontractor_items.remove(sub_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={"deleted": True, "item_id": str(item_id)},
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs={"item_id": str(item_id)},
        outputs={"subcontractors_total": str(estimate.subcontractors_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Permit Items
# ============================================================

@router.post("/{estimate_id}/permits", response_model=ResponseEnvelope, status_code=status.HTTP_201_CREATED)
async def add_permit_item(
    estimate_id: UUID,
    req: PermitItemCreate,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Add permit item to estimate."""
    logger.info("estimates.permit.add", estimate_id=str(estimate_id), permit_type=req.permit_type)

    estimate = await _get_estimate_with_items(estimate_id, db)

    permit_item = PermitItem(
        id=uuid4(),
        estimate_id=estimate_id,
        permit_type=req.permit_type,
        jurisdiction=req.jurisdiction,
        description=req.description,
        amount=req.amount,
        permit_number=req.permit_number,
        notes=req.notes,
        sort_order=req.sort_order,
    )

    db.add(permit_item)
    estimate.permit_items.append(permit_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(permit_item)

    response = PermitItemResponse.model_validate(permit_item)

    return make_envelope(
        result=response.model_dump(),
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs=req.model_dump(),
        outputs={"permits_total": str(estimate.permits_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@router.delete("/{estimate_id}/permits/{item_id}", response_model=ResponseEnvelope)
async def delete_permit_item(
    estimate_id: UUID,
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Delete permit item."""
    estimate = await _get_estimate_with_items(estimate_id, db)

    permit_item = next((i for i in estimate.permit_items if i.id == item_id), None)
    if not permit_item:
        raise HTTPException(status_code=404, detail=f"Permit item {item_id} not found")

    await db.delete(permit_item)
    estimate.permit_items.remove(permit_item)
    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={"deleted": True, "item_id": str(item_id)},
        assumptions=["Estimate totals recalculated"],
        confidence=0.95,
        inputs={"item_id": str(item_id)},
        outputs={"permits_total": str(estimate.permits_total)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Recalculate Endpoint
# ============================================================

@router.post("/{estimate_id}/calculate", response_model=ResponseEnvelope)
async def recalculate_estimate(
    estimate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Force recalculation of all estimate totals."""
    logger.info("estimates.calculate", estimate_id=str(estimate_id))

    estimate = await _get_estimate_with_items(estimate_id, db)

    _recalculate_estimate(estimate)
    estimate.updated_at = datetime.now(UTC)

    await db.commit()

    return make_envelope(
        result={
            "id": str(estimate.id),
            "labor_total": str(estimate.labor_total),
            "materials_total": str(estimate.materials_total),
            "subcontractors_total": str(estimate.subcontractors_total),
            "permits_total": str(estimate.permits_total),
            "direct_cost": str(estimate.direct_cost),
            "overhead_amount": str(estimate.overhead_amount),
            "profit_amount": str(estimate.profit_amount),
            "sell_price": str(estimate.sell_price),
            "quoted_price": str(estimate.quoted_price),
            "gross_margin_percent": str(estimate.gross_margin_percent),
        },
        assumptions=["All totals recalculated from line items"],
        confidence=0.99,
        inputs={"estimate_id": str(estimate_id)},
        outputs={"sell_price": str(estimate.sell_price)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Work Codes Catalog
# ============================================================

work_codes_router = APIRouter(prefix="/api/v1/work-codes", tags=["catalog"])


@work_codes_router.get("/", response_model=ResponseEnvelope)
async def list_work_codes(
    category: LaborCategory | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """List work codes from catalog."""
    logger.info("work_codes.list", category=category, active_only=active_only)

    query = select(WorkCode)
    if category:
        query = query.where(WorkCode.category == category)
    if active_only:
        query = query.where(WorkCode.is_active == True)
    query = query.order_by(WorkCode.code)

    result = await db.execute(query)
    codes = result.scalars().all()

    response = [WorkCodeResponse.model_validate(c).model_dump() for c in codes]

    return make_envelope(
        result={"work_codes": response, "count": len(response)},
        assumptions=[],
        confidence=0.95,
        inputs={"category": category, "active_only": active_only},
        outputs={"count": len(response)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# Material Catalog
# ============================================================

materials_router = APIRouter(prefix="/api/v1/materials", tags=["catalog"])


@materials_router.get("/catalog", response_model=ResponseEnvelope)
async def search_material_catalog(
    query: str | None = Query(None, min_length=2),
    category: MaterialCategory | None = Query(None),
    vendor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Search material catalog."""
    logger.info("materials.catalog.search", query=query, category=category, vendor=vendor)

    stmt = select(MaterialCatalog).where(MaterialCatalog.is_active == True)

    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            (MaterialCatalog.part_number.ilike(search_pattern))
            | (MaterialCatalog.description.ilike(search_pattern))
        )
    if category:
        stmt = stmt.where(MaterialCatalog.category == category)
    if vendor:
        stmt = stmt.where(MaterialCatalog.preferred_vendor.ilike(f"%{vendor}%"))

    stmt = stmt.order_by(MaterialCatalog.part_number).limit(limit)

    result = await db.execute(stmt)
    materials = result.scalars().all()

    response = [MaterialCatalogResponse.model_validate(m).model_dump() for m in materials]

    return make_envelope(
        result={"materials": response, "count": len(response)},
        assumptions=["Results filtered to active items only"],
        confidence=0.95,
        inputs={"query": query, "category": category, "vendor": vendor},
        outputs={"count": len(response)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


@materials_router.get("/catalog/{part_number}", response_model=ResponseEnvelope)
async def get_material_by_part_number(
    part_number: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Get material details by part number."""
    logger.info("materials.catalog.get", part_number=part_number)

    result = await db.execute(
        select(MaterialCatalog).where(MaterialCatalog.part_number == part_number)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {part_number} not found",
        )

    response = MaterialCatalogResponse.model_validate(material)

    return make_envelope(
        result=response.model_dump(),
        assumptions=[],
        confidence=0.95,
        inputs={"part_number": part_number},
        outputs={"unit_cost": str(material.unit_cost)},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )


# ============================================================
# AI Suggestions (Stub)
# ============================================================

@router.post("/{estimate_id}/ai-suggest", response_model=ResponseEnvelope)
async def get_ai_suggestions(
    estimate_id: UUID,
    req: AISuggestionRequest,
    db: AsyncSession = Depends(get_db),
) -> ResponseEnvelope:
    """Get AI-powered suggestions for labor and materials.

    TODO: Integrate with RAG system for similar project lookup.
    """
    logger.info("estimates.ai_suggest", estimate_id=str(estimate_id), sign_type=req.sign_type)

    # Placeholder response - will be enhanced with RAG integration
    return make_envelope(
        result={
            "suggested_labor": [],
            "suggested_materials": [],
            "similar_projects": [],
            "confidence": 0.0,
            "notes": ["AI suggestions not yet implemented - placeholder response"],
        },
        assumptions=["AI suggestion system pending RAG integration"],
        confidence=0.5,
        inputs=req.model_dump(),
        outputs={"suggestions_count": 0},
        code_version=get_code_version(),
        model_config=get_model_config(),
    )
