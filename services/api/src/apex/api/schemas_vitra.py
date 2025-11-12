"""Pydantic schemas for VITRA vision analysis API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ===== Enums =====

class InspectionStatus(str, Enum):
    """Inspection processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InspectionSeverity(str, Enum):
    """Issue severity level."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ComponentType(str, Enum):
    """Component types for recognition."""

    POLE = "pole"
    BASE_PLATE = "base_plate"
    ANCHOR_BOLT = "anchor_bolt"
    CABINET = "cabinet"
    WELD = "weld"
    FASTENER = "fastener"
    FOUNDATION = "foundation"
    OTHER = "other"


class FabricationTask(str, Enum):
    """Robotic fabrication task types."""

    WELDING = "welding"
    CUTTING = "cutting"
    DRILLING = "drilling"
    ASSEMBLY = "assembly"
    INSPECTION = "inspection"
    PACKAGING = "packaging"


# ===== Vision Inspection Schemas =====

class DetectedIssue(BaseModel):
    """Individual issue detected in inspection."""

    type: str = Field(..., description="Issue type (e.g., 'corrosion', 'crack')")
    severity: InspectionSeverity
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    location: dict[str, float] | None = Field(None, description="Bounding box {x, y, w, h}")
    description: str
    recommendation: str | None = None


class StructuralAssessment(BaseModel):
    """Structural condition assessment."""

    overall_condition: str
    estimated_remaining_life_years: float | None = None
    load_capacity_retained_pct: float | None = Field(None, ge=0, le=100)
    critical_components: list[dict[str, Any]] | None = None


class InspectionCreateRequest(BaseModel):
    """Request to create new vision inspection."""

    project_id: str | None = None
    sign_id: str | None = None
    inspection_type: str = Field("periodic", description="'initial', 'periodic', 'damage_assessment'")  # noqa: E501
    media_urls: list[str] = Field(..., min_length=1, description="URLs to images/videos")
    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None
    notes: str | None = None


class InspectionResponse(BaseModel):
    """Vision inspection result."""

    id: str
    project_id: str | None
    sign_id: str | None
    inspector_id: str
    inspection_type: str
    status: InspectionStatus

    media_urls: list[str]
    detected_issues: list[DetectedIssue] | None = None
    structural_assessment: StructuralAssessment | None = None
    safety_score: float | None = Field(None, ge=0, le=100)
    maintenance_recommendations: list[str] | None = None

    latitude: float | None = None
    longitude: float | None = None
    location_name: str | None = None

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class IssueResponse(BaseModel):
    """Inspection issue detail."""

    id: str
    inspection_id: str
    issue_type: str
    severity: InspectionSeverity
    confidence: float
    media_index: int
    bounding_box: dict[str, float] | None
    timestamp_sec: float | None
    description: str
    affected_component: ComponentType | None
    estimated_repair_cost: float | None
    priority_rank: int | None
    resolved: bool
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime


# ===== Installation Video Schemas =====

class ActionTimelineEntry(BaseModel):
    """Single action in installation timeline."""

    timestamp: float = Field(..., description="Timestamp in seconds")
    action: str
    duration_sec: float | None = None
    quality: str | None = None


class ProcedureCompliance(BaseModel):
    """Installation procedure compliance."""

    overall_score: float = Field(..., ge=0, le=100)
    steps_completed: int
    steps_total: int
    deviations: list[dict[str, Any]] | None = None


class InstallationVideoCreateRequest(BaseModel):
    """Request to analyze installation video."""

    project_id: str
    installation_phase: str = Field(..., description="'foundation', 'pole_erection', 'cabinet_mount', etc.")  # noqa: E501
    video_url: str
    notes: str | None = None


class InstallationVideoResponse(BaseModel):
    """Installation video analysis result."""

    id: str
    project_id: str
    installation_phase: str
    status: InspectionStatus

    video_url: str
    duration_sec: float | None
    uploaded_by: str

    action_timeline: list[ActionTimelineEntry] | None = None
    procedure_compliance: ProcedureCompliance | None = None
    safety_violations: list[dict[str, Any]] | None = None
    quality_score: float | None = Field(None, ge=0, le=100)
    completion_percentage: float | None = Field(None, ge=0, le=100)

    generated_report: dict[str, Any] | None = None
    report_pdf_url: str | None = None

    created_at: datetime
    updated_at: datetime
    analyzed_at: datetime | None = None


# ===== Component Recognition Schemas =====

class DetectedComponent(BaseModel):
    """Detected component in image."""

    type: ComponentType
    material: str | None = None
    shape: str | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    dimensions: dict[str, float] | None = None
    location: dict[str, float] | None = None
    condition: str | None = None


class DimensionVerification(BaseModel):
    """Dimension measurement verification."""

    measurement_method: str
    accuracy_mm: float
    verified_dimensions: bool
    tolerance_met: bool


class BOMValidation(BaseModel):
    """BOM validation result."""

    expected_items: list[dict[str, Any]]
    match_score: float = Field(..., ge=0.0, le=1.0)
    discrepancies: list[str]
    validation_passed: bool


class ComponentRecognitionRequest(BaseModel):
    """Request to recognize components."""

    project_id: str | None = None
    bom_id: str | None = None
    image_url: str
    expected_components: list[dict[str, Any]] | None = None
    notes: str | None = None


class ComponentRecognitionResponse(BaseModel):
    """Component recognition result."""

    id: str
    project_id: str | None
    bom_id: str | None
    status: InspectionStatus

    image_url: str
    uploaded_by: str

    detected_components: list[DetectedComponent] | None = None
    material_analysis: dict[str, Any] | None = None
    dimension_verification: DimensionVerification | None = None
    quality_assessment: dict[str, Any] | None = None

    bom_match_score: float | None = Field(None, ge=0, le=1)
    discrepancies: list[str] | None = None
    validation_passed: bool | None = None

    created_at: datetime
    analyzed_at: datetime | None = None


# ===== AR Design Review Schemas =====

class ClearanceAnalysis(BaseModel):
    """Clearance analysis result."""

    overhead_clearance_ft: float
    min_required_ft: float
    clearance_ok: bool
    nearby_obstacles: list[dict[str, Any]] | None = None


class VisualImpactAssessment(BaseModel):
    """Visual impact assessment."""

    visibility_score: float = Field(..., ge=0, le=100)
    viewing_angles: list[str]
    lighting_conditions: str | None = None
    recommended_illumination: str | None = None


class SiteConstraints(BaseModel):
    """Site constraint analysis."""

    soil_type: str | None = None
    water_table_ft: float | None = None
    bedrock_depth_ft: float | None = None
    slope_grade_pct: float | None = None
    foundation_recommendation: str | None = None


class ARDesignReviewRequest(BaseModel):
    """Request for AR design review."""

    project_id: str
    site_photo_url: str
    design_spec: dict[str, Any] = Field(..., description="Sign design specifications")
    camera_metadata: dict[str, Any] | None = None
    latitude: float | None = None
    longitude: float | None = None
    notes: str | None = None


class ARDesignReviewResponse(BaseModel):
    """AR design review result."""

    id: str
    project_id: str
    reviewer_id: str

    site_photo_url: str
    design_overlay_url: str | None = None
    design_spec: dict[str, Any]

    feasibility_score: float | None = Field(None, ge=0, le=100)
    clearance_analysis: ClearanceAnalysis | None = None
    visual_impact_assessment: VisualImpactAssessment | None = None
    site_constraints: SiteConstraints | None = None
    recommendations: list[str] | None = None

    latitude: float | None = None
    longitude: float | None = None

    created_at: datetime
    reviewed_at: datetime | None = None


# ===== Robotic Fabrication Schemas =====

class VLAAction(BaseModel):
    """Vision-Language-Action for robot."""

    action: str
    params: dict[str, Any]


class QualityCheck(BaseModel):
    """Quality check result."""

    check_type: str
    passed: bool
    measurement: float | None = None
    tolerance: float | None = None


class RoboticFabricationRequest(BaseModel):
    """Request for robotic fabrication session."""

    project_id: str | None = None
    component_id: str | None = None
    robot_id: str
    task_type: FabricationTask
    task_specification: dict[str, Any] = Field(..., description="Task parameters")
    notes: str | None = None


class RoboticFabricationResponse(BaseModel):
    """Robotic fabrication session result."""

    id: str
    project_id: str | None
    component_id: str | None
    robot_id: str
    task_type: FabricationTask
    status: InspectionStatus

    task_specification: dict[str, Any]
    vla_model_version: str

    action_sequence: list[VLAAction] | None = None
    video_recording_url: str | None = None
    sensor_data: dict[str, Any] | None = None

    quality_checks: list[QualityCheck] | None = None
    defects_detected: list[dict[str, Any]] | None = None
    pass_fail_status: bool | None = None

    cycle_time_sec: float | None = None
    error_count: int = 0
    retry_count: int = 0

    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
