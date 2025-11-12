"""INSA API Endpoints - Integrated Neuro-Symbolic Architecture.

Provides:
- Production scheduling with hybrid AI reasoning
- Schedule explanations (PE-stampable)
- VITRA-driven adaptive rescheduling
- Knowledge base queries
- Constraint validation
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Import INSA modules (dynamic path required for domain modules)
_domains_path = Path(__file__).parent.parent.parent / "domains" / "signage"
if str(_domains_path) not in sys.path:
    sys.path.insert(0, str(_domains_path))

from insa_scheduler import get_production_scheduler

from ..common.envelope import make_envelope
from ..common.models import ResponseEnvelope
from ..deps import get_current_user_id

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/insa", tags=["insa-scheduling"])


# ===== Request/Response Schemas =====

class ScheduleProjectRequest(BaseModel):
    """Request to schedule a project."""

    project_id: str
    bom_data: dict[str, Any] = Field(
        ...,
        description="Bill of materials with items and operations",
    )
    constraints: dict[str, Any] | None = Field(
        None,
        description="Additional constraints (deadline, priorities)",
    )


class RescheduleRequest(BaseModel):
    """Request to reschedule based on VITRA feedback."""

    project_id: str
    current_schedule: dict[str, Any]
    vitra_data: dict[str, Any] = Field(
        ...,
        description="VITRA inspection/video/component data",
    )


class ExplainScheduleRequest(BaseModel):
    """Request for schedule explanation."""

    project_id: str
    job_id: str


# ===== Endpoints =====

@router.post("/schedule", response_model=ResponseEnvelope)
async def schedule_project(
    request: ScheduleProjectRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ResponseEnvelope:
    """Generate optimized production schedule using INSA hybrid reasoning.

    **Features:**
    - Symbolic constraint satisfaction (AISC/ASCE compliance)
    - Neural pattern learning from historical projects
    - Explainable decisions with reasoning trace
    - Provably correct schedules (PE-stampable)

    **Input BOM Format:**
    ```json
    {
      "items": [
        {
          "id": "item_1",
          "name": "HSS 6x6x1/4 pole",
          "operations": [
            {"type": "cut", "duration_min": 30},
            {"type": "weld", "duration_min": 45},
            {"type": "inspect", "duration_min": 15}
          ]
        }
      ]
    }
    ```

    **Returns:**
    - Detailed operation schedule with start/end times
    - Resource assignments (machines, workers)
    - Makespan and completion estimate
    - Reasoning trace showing applied rules
    - Constraint validation results
    """
    logger.info(
        "insa.schedule.request",
        user_id=user_id,
        project_id=request.project_id,
    )

    try:
        scheduler = get_production_scheduler()

        result = await scheduler.schedule_project(
            project_id=request.project_id,
            bom_data=request.bom_data,
            constraints=request.constraints,
        )

        logger.info(
            "insa.schedule.success",
            project_id=request.project_id,
            operations=len(result["schedule"]["operations"]),
            makespan_hours=result["metadata"]["makespan_hours"],
        )

        assumptions = [
            "Using INSA hybrid neuro-symbolic scheduling",
            f"Applied {len(scheduler.kb.rules)} engineering constraint rules",
            "Schedule validated against AISC 360-22 and ASCE 7-22",
        ]

        if not result["metadata"]["validation"]["valid"]:
            assumptions.append(
                f"WARNING: {len(result['metadata']['validation']['violations'])} "
                "constraints could not be satisfied",
            )

        return make_envelope(
            result=result,
            confidence=result["metadata"].get("confidence", 0.9),
            assumptions=assumptions,
        )

    except Exception as e:
        logger.exception("insa.schedule.error", error=str(e), project_id=request.project_id)
        raise HTTPException(status_code=500, detail=f"Scheduling error: {e!s}") from e


@router.post("/reschedule", response_model=ResponseEnvelope)
async def reschedule_with_vitra(
    request: RescheduleRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ResponseEnvelope:
    """Adaptive rescheduling based on VITRA vision feedback.

    **Use Cases:**
    1. **Quality Issue Detected**
       - VITRA inspection finds defect
       - INSA adjusts downstream processes
       - Adds quality control checkpoints

    2. **Equipment Condition Change**
       - VITRA detects machine wear
       - INSA reallocates work to healthy equipment
       - Schedules maintenance

    3. **Worker Skill Assessment**
       - VITRA analyzes installation video
       - INSA reassigns based on demonstrated skills
       - Optimizes training opportunities

    **VITRA Data Format:**
    ```json
    {
      "source": "inspection",
      "id": "insp_123",
      "result": {
        "detected_issues": [...],
        "safety_score": 85.5
      },
      "reason": "quality_feedback"
    }
    ```

    **Returns:**
    - Revised schedule with VITRA-driven changes
    - Affected job IDs
    - Adaptive reasoning explanation
    """
    logger.info(
        "insa.reschedule.request",
        user_id=user_id,
        project_id=request.project_id,
        vitra_source=request.vitra_data.get("source"),
    )

    try:
        scheduler = get_production_scheduler()

        result = await scheduler.reschedule_with_vitra_feedback(
            project_id=request.project_id,
            current_schedule=request.current_schedule,
            vitra_data=request.vitra_data,
        )

        logger.info(
            "insa.reschedule.success",
            project_id=request.project_id,
            affected_jobs=len(result["metadata"]["affected_jobs"]),
        )

        return make_envelope(
            result=result,
            confidence=result["metadata"].get("confidence", 0.85),
            assumptions=[
                "Adaptive rescheduling triggered by VITRA feedback",
                "Knowledge base updated with new patterns",
                f"Affected {len(result['metadata']['affected_jobs'])} operations",
            ],
        )

    except Exception as e:
        logger.exception("insa.reschedule.error", error=str(e), project_id=request.project_id)
        raise HTTPException(status_code=500, detail=f"Rescheduling error: {e!s}") from e


@router.post("/explain", response_model=ResponseEnvelope)
async def explain_schedule_decision(
    request: ExplainScheduleRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ResponseEnvelope:
    """Generate human-readable explanation for scheduling decision.

    **Purpose:**
    - PE stamp compliance (auditable reasoning)
    - Client transparency
    - Regulatory documentation
    - Continuous improvement analysis

    **Explanation Includes:**
    1. **Symbolic Reasoning:**
       - Which AISC/ASCE rules applied
       - Constraint satisfaction logic
       - Hard vs. soft constraints

    2. **Neural Reasoning:**
       - Similar historical projects (similarity scores)
       - Learned patterns and duration estimates
       - Quality risk predictions

    3. **VITRA-Learned Constraints:**
       - Vision-derived quality rules
       - Safety patterns from installation videos
       - Equipment condition factors

    **Returns:**
    - Natural language explanation
    - Structured reasoning trace
    - Confidence score
    - Applied rules list
    """
    logger.info(
        "insa.explain.request",
        user_id=user_id,
        project_id=request.project_id,
        job_id=request.job_id,
    )

    try:
        scheduler = get_production_scheduler()

        result = scheduler.get_schedule_explanation(
            project_id=request.project_id,
            job_id=request.job_id,
        )

        logger.info(
            "insa.explain.success",
            job_id=request.job_id,
            confidence=result.get("confidence", 1.0),
        )

        return make_envelope(
            result=result,
            confidence=result.get("confidence", 1.0),
            assumptions=["Explanation generated from INSA reasoning trace"],
        )

    except Exception as e:
        logger.exception("insa.explain.error", error=str(e), job_id=request.job_id)
        raise HTTPException(status_code=500, detail=f"Explanation error: {e!s}") from e


@router.get("/knowledge-base/stats", response_model=ResponseEnvelope)
async def get_knowledge_base_stats(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ResponseEnvelope:
    """Get INSA knowledge base statistics.

    **Returns:**
    - Total rules (by source: AISC, ASCE, AWS, IBC, VITRA, etc.)
    - Knowledge graph nodes (jobs, machines, operations)
    - Neural embeddings count
    - Recent updates
    """
    logger.info("insa.kb_stats.request", user_id=user_id)

    try:
        scheduler = get_production_scheduler()
        kb = scheduler.kb

        # Aggregate stats
        rules_by_source = {}
        hard_constraints = 0
        soft_preferences = 0

        for rule in kb.rules.values():
            rules_by_source[rule.source] = rules_by_source.get(rule.source, 0) + 1
            if rule.hard_constraint:
                hard_constraints += 1
            else:
                soft_preferences += 1

        nodes_by_type = {}
        for node in kb.nodes.values():
            nodes_by_type[node.entity_type.value] = nodes_by_type.get(
                node.entity_type.value, 0,
            ) + 1

        embeddings_count = sum(1 for node in kb.nodes.values() if node.embedding)

        result = {
            "total_rules": len(kb.rules),
            "rules_by_source": rules_by_source,
            "hard_constraints": hard_constraints,
            "soft_preferences": soft_preferences,
            "total_nodes": len(kb.nodes),
            "nodes_by_type": nodes_by_type,
            "neural_embeddings": embeddings_count,
            "vitra_updates": scheduler.vitra_bridge.update_count,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        logger.info(
            "insa.kb_stats.success",
            total_rules=result["total_rules"],
            total_nodes=result["total_nodes"],
        )

        return make_envelope(
            result=result,
            confidence=1.0,
            assumptions=["Real-time knowledge base statistics"],
        )

    except Exception as e:
        logger.exception("insa.kb_stats.error", error=str(e))
        raise HTTPException(status_code=500, detail=f"KB stats error: {e!s}") from e


@router.get("/health", response_model=ResponseEnvelope)
async def health_check() -> ResponseEnvelope:
    """INSA system health check.

    **Verifies:**
    - Scheduler initialization
    - Knowledge base loaded
    - VITRA bridge active
    - Rule count > 0
    """
    try:
        scheduler = get_production_scheduler()

        health = {
            "status": "healthy",
            "scheduler_initialized": scheduler is not None,
            "rules_loaded": len(scheduler.kb.rules) > 0,
            "vitra_bridge_active": scheduler.vitra_bridge is not None,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return make_envelope(
            result=health,
            confidence=1.0,
        )

    except Exception as e:
        logger.exception("insa.health.error", error=str(e))
        return make_envelope(
            result={
                "status": "unhealthy",
                "error": str(e),
            },
            confidence=0.0,
        )
