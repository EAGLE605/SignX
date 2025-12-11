"""
Estimator Module - Internal takeoff, BOM, and pricing system.

This module provides comprehensive estimating capabilities:
- Labor breakdown with work codes and hours
- Material BOM with part numbers and quantities
- Subcontractor and permit tracking
- Cost rollup with margin calculations
- KeyedIn integration for pricing sync
"""

from .models import (
    Estimate,
    LaborLineItem,
    MaterialLineItem,
    SubcontractorItem,
    PermitItem,
    EstimateStatus,
)
from .schemas import (
    EstimateCreate,
    EstimateUpdate,
    EstimateResponse,
    LaborLineCreate,
    MaterialLineCreate,
)
from .routes import router, work_codes_router, materials_router
from .keyedin_sync import keyedin_estimator, KeyedInEstimatorClient

__all__ = [
    "Estimate",
    "LaborLineItem",
    "MaterialLineItem",
    "SubcontractorItem",
    "PermitItem",
    "EstimateStatus",
    "EstimateCreate",
    "EstimateUpdate",
    "EstimateResponse",
    "LaborLineCreate",
    "MaterialLineCreate",
    "router",
    "work_codes_router",
    "materials_router",
    "keyedin_estimator",
    "KeyedInEstimatorClient",
]
