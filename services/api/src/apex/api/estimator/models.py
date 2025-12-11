"""
Estimator data models - SQLAlchemy ORM models for estimates, labor, and materials.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for estimator models."""
    pass


class EstimateStatus(str, enum.Enum):
    """Estimate lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"  # Converted to production job


class LaborCategory(str, enum.Enum):
    """Labor work categories."""
    FABRICATION = "fabrication"
    ENGINEERING = "engineering"
    INSTALLATION = "installation"
    ADMIN = "admin"


class MaterialCategory(str, enum.Enum):
    """Material categories for BOM."""
    CABINET = "cabinet"
    ELECTRICAL = "electrical"
    LETTERS = "letters"
    FOUNDATION = "foundation"
    PAINT = "paint"
    HARDWARE = "hardware"
    VINYL = "vinyl"
    NEON = "neon"
    STRUCTURAL = "structural"
    OTHER = "other"


class UnitOfMeasure(str, enum.Enum):
    """Standard units of measure."""
    EA = "EA"       # Each
    LF = "LF"       # Linear Feet
    SF = "SF"       # Square Feet
    CY = "CY"       # Cubic Yards
    GAL = "GAL"     # Gallon
    QT = "QT"       # Quart
    LB = "LB"       # Pound
    KIT = "KIT"     # Kit
    ROLL = "ROLL"   # Roll
    SPOOL = "SPOOL" # Spool
    PK = "PK"       # Pack
    HR = "HR"       # Hour
    SET = "SET"     # Set


class Estimate(Base):
    """
    Main estimate/quote record.

    Contains header info and totals. Line items stored in related tables.
    """
    __tablename__ = "estimates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True
    )

    # Status
    status: Mapped[EstimateStatus] = mapped_column(
        Enum(EstimateStatus), default=EstimateStatus.DRAFT
    )

    # Customer Info
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Project Info
    project_name: Mapped[str] = mapped_column(String(200))
    job_site_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Sign Specifications (JSON for flexibility)
    sign_specs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Expected: {type, dimensions, face_count, illumination, mounting, materials}

    # Engineering Data
    wind_speed_mph: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1), nullable=True)
    exposure_category: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Labor Totals
    labor_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    labor_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    labor_burden_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=25)
    labor_burden_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    labor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Materials Totals
    materials_subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    materials_tax_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=7)
    materials_tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    materials_freight: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    materials_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Subcontractors & Permits
    subcontractors_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    permits_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Cost Summary
    direct_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    overhead_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=15)
    overhead_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    profit_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=20)
    profit_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Final Pricing
    sell_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    quoted_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gross_margin_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)

    # Notes
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Validity
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # KeyedIn Integration
    keyedin_quote_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    keyedin_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Audit
    created_by: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    labor_items: Mapped[list["LaborLineItem"]] = relationship(
        "LaborLineItem", back_populates="estimate", cascade="all, delete-orphan"
    )
    material_items: Mapped[list["MaterialLineItem"]] = relationship(
        "MaterialLineItem", back_populates="estimate", cascade="all, delete-orphan"
    )
    subcontractor_items: Mapped[list["SubcontractorItem"]] = relationship(
        "SubcontractorItem", back_populates="estimate", cascade="all, delete-orphan"
    )
    permit_items: Mapped[list["PermitItem"]] = relationship(
        "PermitItem", back_populates="estimate", cascade="all, delete-orphan"
    )

    def calculate_totals(self) -> None:
        """Recalculate all totals from line items."""
        # Labor
        self.labor_hours = sum(item.hours for item in self.labor_items)
        self.labor_subtotal = sum(item.extended for item in self.labor_items)
        self.labor_burden_amount = self.labor_subtotal * (self.labor_burden_percent / 100)
        self.labor_total = self.labor_subtotal + self.labor_burden_amount

        # Materials
        self.materials_subtotal = sum(item.extended for item in self.material_items)
        self.materials_tax_amount = self.materials_subtotal * (self.materials_tax_percent / 100)
        self.materials_total = self.materials_subtotal + self.materials_tax_amount + self.materials_freight

        # Subs & Permits
        self.subcontractors_total = sum(item.amount for item in self.subcontractor_items)
        self.permits_total = sum(item.amount for item in self.permit_items)

        # Direct Cost
        self.direct_cost = (
            self.labor_total +
            self.materials_total +
            self.subcontractors_total +
            self.permits_total
        )

        # Overhead & Profit
        self.overhead_amount = self.direct_cost * (self.overhead_percent / 100)
        subtotal_with_overhead = self.direct_cost + self.overhead_amount
        self.profit_amount = subtotal_with_overhead * (self.profit_percent / 100)

        # Sell Price
        self.sell_price = subtotal_with_overhead + self.profit_amount

        # If quoted price not manually set, use sell price
        if not self.quoted_price or self.quoted_price == 0:
            self.quoted_price = self.sell_price

        # Gross Margin
        if self.quoted_price > 0:
            self.gross_margin_percent = (
                (self.quoted_price - self.direct_cost) / self.quoted_price * 100
            )


class LaborLineItem(Base):
    """
    Labor line item with work code, hours, and rate.
    """
    __tablename__ = "estimate_labor_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id", ondelete="CASCADE")
    )

    # Work Code
    work_code: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[LaborCategory] = mapped_column(Enum(LaborCategory))

    # Hours & Rate
    hours: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    extended: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # hours * rate

    # Optional
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="labor_items")

    def calculate_extended(self) -> None:
        """Calculate extended cost."""
        self.extended = self.hours * self.rate


class MaterialLineItem(Base):
    """
    Material/BOM line item with part number, quantity, and pricing.
    """
    __tablename__ = "estimate_material_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id", ondelete="CASCADE")
    )

    # Part Info
    part_number: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[MaterialCategory] = mapped_column(Enum(MaterialCategory))

    # Quantity & Pricing
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    unit: Mapped[UnitOfMeasure] = mapped_column(Enum(UnitOfMeasure))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    extended: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # qty * unit_cost

    # Vendor Info
    vendor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vendor_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # KeyedIn Integration
    keyedin_item_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    keyedin_price_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Optional
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="material_items")

    def calculate_extended(self) -> None:
        """Calculate extended cost."""
        self.extended = self.quantity * self.unit_cost


class SubcontractorItem(Base):
    """
    Subcontractor line item.
    """
    __tablename__ = "estimate_subcontractor_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id", ondelete="CASCADE")
    )

    # Subcontractor Info
    vendor_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(500))
    trade: Mapped[str] = mapped_column(String(100))  # electrical, concrete, crane, etc.

    # Pricing
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    # Optional
    quote_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quote_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="subcontractor_items")


class PermitItem(Base):
    """
    Permit and fee line item.
    """
    __tablename__ = "estimate_permit_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    estimate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("estimates.id", ondelete="CASCADE")
    )

    # Permit Info
    permit_type: Mapped[str] = mapped_column(String(100))  # sign, electrical, building, etc.
    jurisdiction: Mapped[str] = mapped_column(String(200))  # City of Des Moines, etc.
    description: Mapped[str] = mapped_column(String(500))

    # Pricing
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    # Optional
    permit_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    estimate: Mapped["Estimate"] = relationship("Estimate", back_populates="permit_items")


class WorkCode(Base):
    """
    Standard work codes for labor estimation.
    """
    __tablename__ = "work_codes"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[LaborCategory] = mapped_column(Enum(LaborCategory))
    default_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    typical_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class MaterialCatalog(Base):
    """
    Material catalog/master for quick lookup.
    """
    __tablename__ = "material_catalog"

    part_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(500))
    category: Mapped[MaterialCategory] = mapped_column(Enum(MaterialCategory))
    unit: Mapped[UnitOfMeasure] = mapped_column(Enum(UnitOfMeasure))

    # Pricing
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    last_cost_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Vendor
    preferred_vendor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vendor_part_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # KeyedIn
    keyedin_item_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
