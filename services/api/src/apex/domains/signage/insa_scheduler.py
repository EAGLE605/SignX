"""INSA Production Scheduler for Sign Manufacturing.

Integrates:
- INSA knowledge base (symbolic rules + neural embeddings)
- SignX BOM and project data
- VITRA vision feedback
- AISC/ASCE compliance constraints

Produces:
- Optimized job shop schedules
- Explainable decisions (PE-stampable)
- Real-time adaptation to shop floor changes
- Quality-aware resource allocation
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog
from insa_core import EntityType, HybridScheduler, KnowledgeNode, get_knowledge_base
from insa_rules import load_all_rules
from insa_vitra_bridge import create_vitra_insa_bridge

logger = structlog.get_logger(__name__)


class SignXProductionScheduler:
    """INSA-powered production scheduler for sign manufacturing."""

    def __init__(self) -> None:
        # Initialize INSA components
        self.kb = get_knowledge_base()
        load_all_rules(self.kb)

        self.scheduler = HybridScheduler(self.kb)
        self.vitra_bridge = create_vitra_insa_bridge(self.kb)

        logger.info(
            "insa.scheduler.init",
            rules=len(self.kb.rules),
            nodes=len(self.kb.nodes),
        )

    async def schedule_project(
        self,
        project_id: str,
        bom_data: dict[str, Any],
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate production schedule for sign project.

        Args:
            project_id: Project identifier
            bom_data: Bill of materials with operations
            constraints: Additional constraints (deadlines, resource limits)

        Returns:
            Optimized schedule with reasoning trace

        """
        start_time = datetime.utcnow()

        logger.info(
            "insa.schedule_project.start",
            project_id=project_id,
            bom_items=len(bom_data.get("items", [])),
        )

        # 1. Convert BOM to job shop representation
        jobs = self._bom_to_jobs(project_id, bom_data)

        # 2. Add project to knowledge graph
        self._add_project_to_kb(project_id, bom_data, constraints or {})

        # 3. Generate schedule using hybrid reasoning
        schedule, metadata = await self.scheduler.schedule(jobs)

        # 4. Post-process: add timing, resources, dependencies
        detailed_schedule = self._enrich_schedule(project_id, schedule, bom_data)

        # 5. Validate against AISC/ASCE rules
        validation_result = self._validate_schedule(detailed_schedule)

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        logger.info(
            "insa.schedule_project.complete",
            project_id=project_id,
            elapsed_sec=elapsed,
            operations=len(schedule),
            valid=validation_result["valid"],
        )

        return {
            "project_id": project_id,
            "schedule": detailed_schedule,
            "metadata": {
                **metadata,
                "total_elapsed_sec": elapsed,
                "validation": validation_result,
                "makespan_hours": self._calculate_makespan(detailed_schedule),
                "estimated_completion": self._estimate_completion(detailed_schedule),
            },
        }

    async def reschedule_with_vitra_feedback(
        self,
        project_id: str,
        current_schedule: dict[str, Any],
        vitra_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Reschedule based on VITRA vision feedback.

        Use cases:
        - Quality issue detected → adjust downstream processes
        - Equipment condition degraded → change resource allocation
        - Worker skill assessment → reassign operations
        """
        logger.info(
            "insa.reschedule.start",
            project_id=project_id,
            vitra_source=vitra_data.get("source"),
        )

        # 1. Update knowledge base with VITRA data
        if vitra_data.get("source") == "inspection":
            await self.vitra_bridge.process_inspection_result(
                vitra_data["id"],
                vitra_data["result"],
            )
        elif vitra_data.get("source") == "installation_video":
            await self.vitra_bridge.process_installation_video(
                vitra_data["id"],
                vitra_data["result"],
            )

        # 2. Extract affected jobs from VITRA feedback
        affected_jobs = self._identify_affected_jobs(current_schedule, vitra_data)

        # 3. Rebuild schedule for affected portion
        jobs_to_reschedule = [
            job for job in current_schedule["operations"]
            if job["job_id"] in affected_jobs
        ]

        # 4. Generate revised schedule
        revised_schedule, metadata = await self.scheduler.schedule(jobs_to_reschedule)

        # 5. Merge with unchanged portions
        final_schedule = self._merge_schedules(
            current_schedule,
            revised_schedule,
            affected_jobs,
        )

        logger.info(
            "insa.reschedule.complete",
            project_id=project_id,
            affected_jobs=len(affected_jobs),
            changes=len(revised_schedule),
        )

        return {
            "project_id": project_id,
            "schedule": final_schedule,
            "metadata": {
                **metadata,
                "affected_jobs": affected_jobs,
                "vitra_triggered": True,
                "adaptive_reason": vitra_data.get("reason", "quality_feedback"),
            },
        }

    def get_schedule_explanation(
        self,
        project_id: str,
        job_id: str,
    ) -> dict[str, Any]:
        """Generate human-readable explanation for scheduling decision.

        For PE stamp compliance and client transparency.
        """
        logger.info(
            "insa.explain.start",
            project_id=project_id,
            job_id=job_id,
        )

        # Retrieve job node from knowledge graph
        job_node = self.kb.get_node(job_id)

        if not job_node:
            return {
                "job_id": job_id,
                "explanation": "Job not found in knowledge base",
                "reasoning_trace": [],
            }

        # Build explanation from provenance
        explanation = []

        # 1. Symbolic reasoning trace
        symbolic_trace = self.scheduler.symbolic.explain_decision(
            "schedule",
            {"job_id": job_id, "job_attributes": job_node.attributes},
        )
        explanation.extend(symbolic_trace)

        # 2. Neural similarity reasoning
        similar_jobs = self.scheduler.neural.predict_similar_jobs(job_id, top_k=3)
        if similar_jobs:
            explanation.append("\nNeural Reasoning (Historical Similarity):")
            for sim_id, similarity, attrs in similar_jobs:
                explanation.append(
                    f"  • Similar to {sim_id} ({similarity:.2%} match) - "
                    f"completed in {attrs.get('actual_duration_min', 'N/A')} min",
                )

        # 3. VITRA-learned constraints
        vitra_rules = [
            r for r in self.kb.rules.values()
            if r.source.startswith("vitra")
        ]
        if vitra_rules:
            explanation.append("\nVITRA-Learned Constraints:")
            for rule in vitra_rules[:3]:  # Top 3
                explanation.append(f"  • {rule.description}")

        return {
            "job_id": job_id,
            "explanation": "\n".join(explanation),
            "reasoning_trace": job_node.provenance,
            "confidence": job_node.confidence,
        }

    # ===== Internal Methods =====

    def _bom_to_jobs(
        self,
        project_id: str,
        bom_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Convert BOM to job shop representation."""
        jobs = []

        for idx, item in enumerate(bom_data.get("items", [])):
            # Extract operations from BOM item
            operations = item.get("operations", [
                {"type": "cut", "duration_min": 30},
                {"type": "weld", "duration_min": 45},
                {"type": "inspect", "duration_min": 15},
            ])

            for op_idx, operation in enumerate(operations):
                job_id = f"{project_id}_item{idx}_op{op_idx}"

                jobs.append({
                    "id": job_id,
                    "project_id": project_id,
                    "bom_item_id": item.get("id", f"item_{idx}"),
                    "operation_type": operation["type"],
                    "estimated_duration_min": operation.get("duration_min", 60),
                    "required_machine": self._get_required_machine(operation["type"]),
                    "required_skills": self._get_required_skills(operation["type"]),
                    "precedence": self._get_precedence(operations, op_idx),
                })

        return jobs

    def _get_required_machine(self, operation_type: str) -> str:
        """Map operation to required machine."""
        machine_map = {
            "cut": "saw",
            "weld": "welder",
            "drill": "drill_press",
            "paint": "paint_booth",
            "assemble": "assembly_table",
            "inspect": "inspection_station",
        }
        return machine_map.get(operation_type, "general")

    def _get_required_skills(self, operation_type: str) -> list[str]:
        """Map operation to required worker skills."""
        skill_map = {
            "weld": ["aws_certified", "structural_welding"],
            "cut": ["saw_operation"],
            "drill": ["precision_machining"],
            "paint": ["coating_application"],
            "assemble": ["assembly"],
            "inspect": ["quality_control", "pe_certification"],
        }
        return skill_map.get(operation_type, [])

    def _get_precedence(
        self,
        operations: list[dict[str, Any]],
        current_idx: int,
    ) -> list[int]:
        """Get precedence constraints for operation."""
        # Simple linear precedence (in production, use DAG)
        if current_idx == 0:
            return []
        return [current_idx - 1]

    def _add_project_to_kb(
        self,
        project_id: str,
        bom_data: dict[str, Any],
        constraints: dict[str, Any],
    ) -> None:
        """Add project to knowledge graph."""
        project_node = KnowledgeNode(
            node_id=project_id,
            entity_type=EntityType.JOB,
            attributes={
                "bom_items": len(bom_data.get("items", [])),
                "deadline": constraints.get("deadline"),
                "priority": constraints.get("priority", "normal"),
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        self.kb.add_node(project_node)

    def _enrich_schedule(
        self,
        project_id: str,
        schedule: list[dict[str, Any]],
        bom_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Add detailed timing and resource information to schedule."""
        operations = []
        current_time = datetime.utcnow()

        for item in schedule:
            duration = item.get("end_time", 60) - item.get("start_time", 0)

            operations.append({
                "job_id": item["job_id"],
                "operation_type": self._extract_operation_type(item["job_id"]),
                "scheduled_start": (
                    current_time + timedelta(minutes=item["start_time"])
                ).isoformat(),
                "scheduled_end": (
                    current_time + timedelta(minutes=item["end_time"])
                ).isoformat(),
                "duration_min": duration,
                "assigned_machine": item.get("assigned_machine", "M1"),
                "assigned_worker": item.get("assigned_worker", "W1"),
                "status": "pending",
            })

        return {
            "project_id": project_id,
            "operations": operations,
            "total_operations": len(operations),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _extract_operation_type(self, job_id: str) -> str:
        """Extract operation type from job ID."""
        # Parse job_id format: project_itemX_opY
        if "_op" in job_id:
            parts = job_id.split("_")
            op_idx = int(parts[-1].replace("op", ""))
            # Map index to operation (simplified)
            ops = ["cut", "weld", "inspect"]
            return ops[op_idx] if op_idx < len(ops) else "unknown"
        return "unknown"

    def _validate_schedule(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """Validate schedule against all constraints."""
        context = {
            "schedule": schedule["operations"],
            "project_id": schedule["project_id"],
        }

        valid, violations = self.scheduler.symbolic.verify_constraints(context)

        return {
            "valid": valid,
            "violations": violations,
            "rules_checked": len(self.kb.rules),
        }

    def _calculate_makespan(self, schedule: dict[str, Any]) -> float:
        """Calculate total schedule duration in hours."""
        if not schedule.get("operations"):
            return 0.0

        max_end = max(
            datetime.fromisoformat(op["scheduled_end"])
            for op in schedule["operations"]
        )
        min_start = min(
            datetime.fromisoformat(op["scheduled_start"])
            for op in schedule["operations"]
        )

        return (max_end - min_start).total_seconds() / 3600.0

    def _estimate_completion(self, schedule: dict[str, Any]) -> str:
        """Estimate project completion date."""
        if not schedule.get("operations"):
            return datetime.utcnow().isoformat()

        max_end = max(
            datetime.fromisoformat(op["scheduled_end"])
            for op in schedule["operations"]
        )

        return max_end.isoformat()

    def _identify_affected_jobs(
        self,
        current_schedule: dict[str, Any],
        vitra_data: dict[str, Any],
    ) -> set[str]:
        """Identify jobs affected by VITRA feedback."""
        affected = set()

        # Extract affected components from VITRA data
        if "detected_issues" in vitra_data.get("result", {}):
            for issue in vitra_data["result"]["detected_issues"]:
                # Find related jobs (simplified)
                component_type = issue.get("affected_component", "")
                for op in current_schedule.get("operations", []):
                    if component_type in op.get("job_id", ""):
                        affected.add(op["job_id"])

        return affected

    def _merge_schedules(
        self,
        current: dict[str, Any],
        revised: list[dict[str, Any]],
        affected_jobs: set[str],
    ) -> dict[str, Any]:
        """Merge revised schedule with unchanged operations."""
        merged_ops = []

        # Keep unchanged operations
        for op in current.get("operations", []):
            if op["job_id"] not in affected_jobs:
                merged_ops.append(op)

        # Add revised operations
        merged_ops.extend(revised)

        # Sort by start time
        merged_ops.sort(key=lambda x: x.get("start_time", 0))

        return {
            **current,
            "operations": merged_ops,
            "revised_at": datetime.utcnow().isoformat(),
        }


# ===== Factory Function =====

_scheduler_instance: SignXProductionScheduler | None = None


def get_production_scheduler() -> SignXProductionScheduler:
    """Get singleton production scheduler."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SignXProductionScheduler()
    return _scheduler_instance
