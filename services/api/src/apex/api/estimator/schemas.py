"""
Estimator Pydantic schemas for API request/response validation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from .models import (
    EstimateStatus,
    LaborCategory,
    MaterialCategory,
    UnitOfMeasure,
)


# ============================================================
# Sign Specifications (embedded in estimate)
# ============================================================

class SignSpecification(BaseModel):
    """Sign specification details."""
    sign_type: str = Field(..., description="monument, pole, channel_letters, cabinet, pylon")
    width_ft: Optional[Decimal] = None
    height_ft: Optional[Decimal] = None
    depth_ft: Optional[Decimal] = None
    face_count: int = Field(default=1, description="1=single, 2=double-sided")
    illumination: Optional[str] = Field(None, description="none, LED, neon, backlit")
    mounting: Optional[str] = Field(None, description="ground, wall, roof, pole")
    materials: Optional[list[str]] = None
    notes: Optional[str] = None


# ============================================================
# Labor Line Item Schemas
# ============================================================

class LaborLineBase(BaseModel):
    """Base labor line item fields."""
    work_code: str = Field(..., max_length=20, description="Work code (e.g., FAB-01)")
    description: str = Field(..., max_length=500)
    category: LaborCategory
    hours: Decimal = Field(..., ge=0, decimal_places=2)
    rate: Decimal = Field(..., ge=0, decimal_places=2)
    notes: Optional[str] = None
    sort_order: int = Field(default=0)


class LaborLineCreate(LaborLineBase):
    """Create labor line item."""
    pass


class LaborLineUpdate(BaseModel):
    """Update labor line item (all fields optional)."""
    work_code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[LaborCategory] = None
    hours: Optional[Decimal] = Field(None, ge=0)
    rate: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class LaborLineResponse(LaborLineBase):
    """Labor line item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_id: UUID
    extended: Decimal
    created_at: datetime
    updated_at: datetime


# ============================================================
# Material Line Item Schemas
# ============================================================

class MaterialLineBase(BaseModel):
    """Base material line item fields."""
    part_number: str = Field(..., max_length=50, description="Part number (e.g., AL-4X8-63)")
    description: str = Field(..., max_length=500)
    category: MaterialCategory
    quantity: Decimal = Field(..., ge=0, decimal_places=3)
    unit: UnitOfMeasure
    unit_cost: Decimal = Field(..., ge=0, decimal_places=4)
    vendor: Optional[str] = Field(None, max_length=200)
    vendor_part_number: Optional[str] = Field(None, max_length=100)
    lead_time_days: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    sort_order: int = Field(default=0)
    is_taxable: bool = Field(default=True)


class MaterialLineCreate(MaterialLineBase):
    """Create material line item."""
    pass


class MaterialLineUpdate(BaseModel):
    """Update material line item (all fields optional)."""
    part_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[MaterialCategory] = None
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit: Optional[UnitOfMeasure] = None
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    vendor: Optional[str] = None
    vendor_part_number: Optional[str] = None
    lead_time_days: Optional[int] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None
    is_taxable: Optional[bool] = None


class MaterialLineResponse(MaterialLineBase):
    """Material line item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_id: UUID
    extended: Decimal
    keyedin_item_id: Optional[str] = None
    keyedin_price_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# Subcontractor Item Schemas
# ============================================================

class SubcontractorItemBase(BaseModel):
    """Base subcontractor item fields."""
    vendor_name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=500)
    trade: str = Field(..., max_length=100, description="electrical, concrete, crane, etc.")
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    quote_number: Optional[str] = Field(None, max_length=100)
    quote_date: Optional[datetime] = None
    notes: Optional[str] = None
    sort_order: int = Field(default=0)


class SubcontractorItemCreate(SubcontractorItemBase):
    """Create subcontractor item."""
    pass


class SubcontractorItemResponse(SubcontractorItemBase):
    """Subcontractor item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Permit Item Schemas
# ============================================================

class PermitItemBase(BaseModel):
    """Base permit item fields."""
    permit_type: str = Field(..., max_length=100, description="sign, electrical, building")
    jurisdiction: str = Field(..., max_length=200, description="City of Des Moines")
    description: str = Field(..., max_length=500)
    amount: Decimal = Field(..., ge=0, decimal_places=2)
    permit_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    sort_order: int = Field(default=0)


class PermitItemCreate(PermitItemBase):
    """Create permit item."""
    pass


class PermitItemResponse(PermitItemBase):
    """Permit item response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_id: UUID
    created_at: datetime
    updated_at: datetime


# ============================================================
# Estimate Schemas
# ============================================================

class EstimateBase(BaseModel):
    """Base estimate fields."""
    # Customer
    customer_name: str = Field(..., max_length=200)
    customer_email: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_company: Optional[str] = Field(None, max_length=200)

    # Project
    project_name: str = Field(..., max_length=200)
    job_site_address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)

    # Sign Specs
    sign_specs: Optional[SignSpecification] = None

    # Engineering
    wind_speed_mph: Optional[Decimal] = Field(None, ge=0, le=200)
    exposure_category: Optional[str] = Field(None, pattern="^[BCD]$")

    # Markup Percentages
    labor_burden_percent: Decimal = Field(default=Decimal("25.00"), ge=0, le=100)
    materials_tax_percent: Decimal = Field(default=Decimal("7.00"), ge=0, le=20)
    materials_freight: Decimal = Field(default=Decimal("0.00"), ge=0)
    overhead_percent: Decimal = Field(default=Decimal("15.00"), ge=0, le=50)
    profit_percent: Decimal = Field(default=Decimal("20.00"), ge=0, le=100)

    # Notes
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    terms_conditions: Optional[str] = None

    # Validity
    valid_days: int = Field(default=30, ge=1, le=365, description="Quote valid for N days")
    lead_time_days: Optional[int] = Field(None, ge=0)


class EstimateCreate(EstimateBase):
    """Create estimate request."""
    project_id: Optional[UUID] = None


class EstimateUpdate(BaseModel):
    """Update estimate request (all fields optional)."""
    status: Optional[EstimateStatus] = None

    # Customer
    customer_name: Optional[str] = Field(None, max_length=200)
    customer_email: Optional[str] = Field(None, max_length=200)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_company: Optional[str] = Field(None, max_length=200)

    # Project
    project_name: Optional[str] = Field(None, max_length=200)
    job_site_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    # Sign Specs
    sign_specs: Optional[SignSpecification] = None

    # Engineering
    wind_speed_mph: Optional[Decimal] = None
    exposure_category: Optional[str] = None

    # Markup Percentages
    labor_burden_percent: Optional[Decimal] = None
    materials_tax_percent: Optional[Decimal] = None
    materials_freight: Optional[Decimal] = None
    overhead_percent: Optional[Decimal] = None
    profit_percent: Optional[Decimal] = None

    # Manual price override
    quoted_price: Optional[Decimal] = Field(None, ge=0)

    # Notes
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    terms_conditions: Optional[str] = None

    # Validity
    valid_days: Optional[int] = None
    lead_time_days: Optional[int] = None


class EstimateSummary(BaseModel):
    """Estimate summary for list views."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_number: str
    status: EstimateStatus
    customer_name: str
    project_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    quoted_price: Decimal
    gross_margin_percent: Decimal
    created_at: datetime
    updated_at: datetime
    valid_until: Optional[datetime] = None


class EstimateResponse(EstimateBase):
    """Full estimate response with all line items."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    estimate_number: str
    project_id: Optional[UUID] = None
    status: EstimateStatus

    # Computed Totals
    labor_hours: Decimal
    labor_subtotal: Decimal
    labor_burden_amount: Decimal
    labor_total: Decimal

    materials_subtotal: Decimal
    materials_tax_amount: Decimal
    materials_total: Decimal

    subcontractors_total: Decimal
    permits_total: Decimal

    direct_cost: Decimal
    overhead_amount: Decimal
    profit_amount: Decimal

    sell_price: Decimal
    quoted_price: Decimal
    gross_margin_percent: Decimal

    valid_until: Optional[datetime] = None

    # KeyedIn
    keyedin_quote_id: Optional[str] = None
    keyedin_synced_at: Optional[datetime] = None

    # Audit
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Line Items
    labor_items: list[LaborLineResponse] = []
    material_items: list[MaterialLineResponse] = []
    subcontractor_items: list[SubcontractorItemResponse] = []
    permit_items: list[PermitItemResponse] = []


# ============================================================
# Work Code Schemas
# ============================================================

class WorkCodeResponse(BaseModel):
    """Work code response."""
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str
    category: LaborCategory
    default_rate: Decimal
    typical_hours: Optional[Decimal] = None
    is_active: bool


# ============================================================
# Material Catalog Schemas
# ============================================================

class MaterialCatalogResponse(BaseModel):
    """Material catalog item response."""
    model_config = ConfigDict(from_attributes=True)

    part_number: str
    description: str
    category: MaterialCategory
    unit: UnitOfMeasure
    unit_cost: Decimal
    last_cost_update: Optional[datetime] = None
    preferred_vendor: Optional[str] = None
    vendor_part_number: Optional[str] = None
    lead_time_days: Optional[int] = None
    is_active: bool
    is_taxable: bool


class MaterialCatalogSearch(BaseModel):
    """Search material catalog request."""
    query: Optional[str] = Field(None, min_length=2, description="Search term")
    category: Optional[MaterialCategory] = None
    vendor: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)


# ============================================================
# AI Suggestion Schemas
# ============================================================

class AISuggestionRequest(BaseModel):
    """Request AI suggestions for estimate."""
    sign_type: str
    dimensions: Optional[dict] = None
    illumination: Optional[str] = None
    mounting: Optional[str] = None


class AISuggestionResponse(BaseModel):
    """AI suggestion response."""
    suggested_labor: list[LaborLineCreate]
    suggested_materials: list[MaterialLineCreate]
    similar_projects: list[dict]
    confidence: float
    notes: list[str]
