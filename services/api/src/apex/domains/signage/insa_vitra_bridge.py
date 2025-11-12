"""
VITRA-INSA Integration Bridge

Connects VITRA vision analysis with INSA knowledge base for:
1. Real-time knowledge updates from vision inspections
2. Quality-aware scheduling based on VITRA data
3. Continuous learning from fabrication/installation feedback
4. Neuro-symbolic manufacturing optimization

This creates a closed-loop AI system where:
- Vision informs scheduling (detected quality issues → adjust processes)
- Symbolic rules guide vision interpretation (what to look for)
- Neural learning adapts from VITRA feedback
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import structlog
from insa_core import (
    EntityType,
    INSAKnowledgeBase,
    KnowledgeNode,
    NeuralEmbedding,
    SymbolicRule,
)

logger = structlog.get_logger(__name__)


class VITRAINSABridge:
    """Bridge between VITRA vision analysis and INSA knowledge base."""

    def __init__(self, kb: INSAKnowledgeBase):
        self.kb = kb
        self.update_count = 0

    async def process_inspection_result(
        self,
        inspection_id: str,
        vitra_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process VITRA inspection result and update INSA knowledge.

        Updates:
        - Component quality embeddings
        - Process reliability scores
        - Constraint rules (if critical issues found)
        - Maintenance scheduling priorities

        Returns:
            Update summary with reasoning trace
        """
        start_time = time.time()

        logger.info(
            "vitra_insa.inspection.start",
            inspection_id=inspection_id,
            safety_score=vitra_result.get("safety_score"),
        )

        updates = {
            "symbolic_updates": [],
            "neural_updates": [],
            "new_constraints": [],
        }

        # 1. Update component quality knowledge (neural)
        if "structural_assessment" in vitra_result:
            self._update_component_quality(
                inspection_id,
                vitra_result["structural_assessment"],
                updates,
            )

        # 2. Process detected issues
        if "detected_issues" in vitra_result:
            for issue in vitra_result["detected_issues"]:
                self._process_detected_issue(inspection_id, issue, updates)

        # 3. Update maintenance schedule (symbolic + neural)
        if "maintenance_recommendations" in vitra_result:
            self._update_maintenance_knowledge(
                inspection_id,
                vitra_result["maintenance_recommendations"],
                updates,
            )

        # 4. Learn from safety score patterns (neural)
        safety_score = vitra_result.get("safety_score")
        if safety_score is not None:
            self._update_safety_patterns(inspection_id, safety_score, updates)

        self.update_count += 1
        elapsed = time.time() - start_time

        logger.info(
            "vitra_insa.inspection.complete",
            inspection_id=inspection_id,
            elapsed_ms=elapsed * 1000,
            symbolic_updates=len(updates["symbolic_updates"]),
            neural_updates=len(updates["neural_updates"]),
        )

        return {
            "inspection_id": inspection_id,
            "updates_applied": updates,
            "total_kb_updates": self.update_count,
            "elapsed_sec": elapsed,
        }

    async def process_installation_video(
        self,
        video_id: str,
        vitra_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process VITRA installation video analysis.

        Learns:
        - Procedure compliance patterns
        - Worker skill levels
        - Process improvement opportunities
        - Safety violation correlations
        """
        logger.info(
            "vitra_insa.installation.start",
            video_id=video_id,
            quality_score=vitra_result.get("quality_score"),
        )

        updates = {
            "procedure_updates": [],
            "worker_skill_updates": [],
            "safety_rule_updates": [],
        }

        # 1. Update procedure compliance knowledge
        if "procedure_compliance" in vitra_result:
            compliance = vitra_result["procedure_compliance"]
            self._update_procedure_knowledge(video_id, compliance, updates)

        # 2. Process safety violations
        if "safety_violations" in vitra_result:
            for violation in vitra_result["safety_violations"]:
                self._process_safety_violation(video_id, violation, updates)

        # 3. Learn from action timeline
        if "action_timeline" in vitra_result:
            self._learn_from_action_timeline(
                video_id,
                vitra_result["action_timeline"],
                updates,
            )

        logger.info(
            "vitra_insa.installation.complete",
            video_id=video_id,
            updates=len(updates["procedure_updates"]),
        )

        return {
            "video_id": video_id,
            "updates_applied": updates,
        }

    async def process_component_recognition(
        self,
        recognition_id: str,
        vitra_result: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process VITRA component recognition result.

        Learns:
        - Component visual signatures
        - Quality grading patterns
        - BOM validation accuracy
        - Supplier quality trends
        """
        logger.info(
            "vitra_insa.component.start",
            recognition_id=recognition_id,
            components=len(vitra_result.get("detected_components", [])),
        )

        updates = {
            "component_signatures": [],
            "quality_patterns": [],
            "bom_accuracy": [],
        }

        # 1. Update component visual embeddings (neural)
        if "detected_components" in vitra_result:
            for component in vitra_result["detected_components"]:
                self._update_component_signature(recognition_id, component, updates)

        # 2. Learn from BOM validation
        bom_validation = vitra_result.get("bom_validation", {})
        if bom_validation.get("validation_passed") is not None:
            self._update_bom_knowledge(recognition_id, bom_validation, updates)

        # 3. Update quality grading patterns
        if "quality_assessment" in vitra_result:
            self._update_quality_grading(
                recognition_id,
                vitra_result["quality_assessment"],
                updates,
            )

        logger.info(
            "vitra_insa.component.complete",
            recognition_id=recognition_id,
            updates=len(updates["component_signatures"]),
        )

        return {
            "recognition_id": recognition_id,
            "updates_applied": updates,
        }

    async def enhance_scheduling_context(
        self,
        base_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Enhance scheduling context with VITRA-learned knowledge.

        Adds:
        - Component quality predictions
        - Process reliability scores
        - Worker skill assessments
        - Equipment condition status
        """
        enhanced = base_context.copy()

        # Add quality predictions from neural embeddings
        if "job_id" in base_context:
            similar_jobs = self.kb.query_similar(
                base_context["job_id"],
                EntityType.JOB,
                top_k=3,
            )

            if similar_jobs:
                enhanced["similar_historical_jobs"] = similar_jobs
                enhanced["predicted_quality_score"] = self._predict_quality_from_similar(
                    similar_jobs
                )

        # Add equipment condition from recent inspections
        if "machine_id" in base_context:
            machine_node = self.kb.get_node(base_context["machine_id"])
            if machine_node:
                enhanced["machine_condition"] = machine_node.attributes.get(
                    "vitra_condition_score", 100
                )

        # Add worker skill levels from installation videos
        if "worker_id" in base_context:
            worker_node = self.kb.get_node(base_context["worker_id"])
            if worker_node:
                enhanced["worker_skill_score"] = worker_node.attributes.get(
                    "vitra_skill_score", 0.85
                )

        return enhanced

    # ===== Internal Update Methods =====

    def _update_component_quality(
        self,
        inspection_id: str,
        assessment: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Update component quality in knowledge base."""
        component_id = f"comp_{inspection_id}"

        # Create or update component node
        node = self.kb.get_node(component_id)
        if not node:
            node = KnowledgeNode(
                node_id=component_id,
                entity_type=EntityType.MATERIAL,
                attributes={
                    "source": "vitra_inspection",
                    "created_at": datetime.utcnow().isoformat(),
                },
            )

        # Update attributes with assessment data
        node.attributes.update({
            "overall_condition": assessment.get("overall_condition", "unknown"),
            "remaining_life_years": assessment.get("estimated_remaining_life_years"),
            "capacity_retained_pct": assessment.get("load_capacity_retained_pct"),
            "last_inspection": datetime.utcnow().isoformat(),
        })

        # Update confidence based on condition
        condition_map = {"excellent": 1.0, "good": 0.9, "fair": 0.7, "poor": 0.5}
        node.confidence = condition_map.get(assessment.get("overall_condition", ""), 0.8)

        self.kb.add_node(node)

        updates["neural_updates"].append(f"Updated component {component_id} quality assessment")

    def _process_detected_issue(
        self,
        inspection_id: str,
        issue: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Process detected issue from VITRA."""
        issue_type = issue.get("type", "unknown")
        severity = issue.get("severity", "low")

        logger.debug(
            "vitra_insa.issue.process",
            inspection_id=inspection_id,
            type=issue_type,
            severity=severity,
        )

        # If critical, add new constraint rule
        if severity == "critical":
            rule = SymbolicRule(
                name=f"avoid_{issue_type}_{inspection_id}",
                description=f"VITRA detected critical {issue_type}: {issue.get('description')}",
                condition=f"context.get('issue_type') != '{issue_type}'",
                hard_constraint=False,  # Warning, not blocker
                source="vitra_learned",
                priority=70,
            )

            self.kb.add_rule(rule)
            updates["new_constraints"].append(rule.name)

        # Update issue frequency statistics (neural learning)
        issue_stats_id = f"issue_stats_{issue_type}"
        stats_node = self.kb.get_node(issue_stats_id)

        if not stats_node:
            stats_node = KnowledgeNode(
                node_id=issue_stats_id,
                entity_type=EntityType.CONSTRAINT,
                attributes={
                    "issue_type": issue_type,
                    "occurrence_count": 0,
                    "severity_distribution": {},
                },
            )

        stats_node.attributes["occurrence_count"] += 1
        severity_dist = stats_node.attributes.get("severity_distribution", {})
        severity_dist[severity] = severity_dist.get(severity, 0) + 1
        stats_node.attributes["severity_distribution"] = severity_dist

        self.kb.add_node(stats_node)

        updates["neural_updates"].append(f"Updated issue statistics for {issue_type}")

    def _update_maintenance_knowledge(
        self,
        inspection_id: str,
        recommendations: list[str],
        updates: dict[str, Any],
    ) -> None:
        """Update maintenance scheduling knowledge."""
        for rec in recommendations:
            # Parse recommendation (simplified)
            if "within" in rec.lower() and "month" in rec.lower():
                # Extract timeframe and create scheduling constraint
                priority = 80 if "6 months" in rec else 90

                rule = SymbolicRule(
                    name=f"maintenance_{inspection_id}",
                    description=f"VITRA maintenance: {rec}",
                    condition="True",  # Always applicable
                    hard_constraint=False,
                    source="vitra_maintenance",
                    priority=priority,
                )

                self.kb.add_rule(rule)
                updates["symbolic_updates"].append(rule.name)

    def _update_safety_patterns(
        self,
        inspection_id: str,
        safety_score: float,
        updates: dict[str, Any],
    ) -> None:
        """Learn safety score patterns (neural)."""
        # Create embedding for safety assessment
        embedding = NeuralEmbedding(
            entity_id=inspection_id,
            entity_type=EntityType.CONSTRAINT,
            embedding_vector=[safety_score / 100.0],  # Normalized
            confidence=0.9,
            learned_from=[inspection_id],
        )

        # Associate with inspection node
        node = KnowledgeNode(
            node_id=inspection_id,
            entity_type=EntityType.JOB,
            embedding=embedding,
            attributes={"safety_score": safety_score},
        )

        self.kb.add_node(node)
        updates["neural_updates"].append(f"Learned safety pattern from {inspection_id}")

    def _update_procedure_knowledge(
        self,
        video_id: str,
        compliance: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Update procedure compliance knowledge."""
        overall_score = compliance.get("overall_score", 0)

        if overall_score < 90:
            # Flag for procedure review
            logger.warning(
                "vitra_insa.low_compliance",
                video_id=video_id,
                score=overall_score,
            )

            updates["procedure_updates"].append(
                f"Low compliance ({overall_score}%) - review recommended"
            )

    def _process_safety_violation(
        self,
        video_id: str,
        violation: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Process safety violation from installation video."""
        violation_type = violation.get("violation", "unknown")

        # Add rule to prevent recurrence
        rule = SymbolicRule(
            name=f"safety_{violation_type}_{video_id}",
            description=f"Prevent {violation_type} (detected in {video_id})",
            condition="True",  # Simplified
            hard_constraint=True,
            source="vitra_safety",
            priority=95,
        )

        self.kb.add_rule(rule)
        updates["safety_rule_updates"].append(rule.name)

    def _learn_from_action_timeline(
        self,
        video_id: str,
        timeline: list[dict[str, Any]],
        updates: dict[str, Any],
    ) -> None:
        """Learn process timing patterns from action timeline."""
        # Build neural representation of process sequence
        for action in timeline:
            action_type = action.get("action", "unknown")
            duration = action.get("duration_sec", 0)

            # Update duration estimates in knowledge base
            # (simplified - in production, use proper time series model)
            logger.debug(
                "vitra_insa.learn_timing",
                action=action_type,
                duration_sec=duration,
            )

        updates["procedure_updates"].append(f"Learned timing from {len(timeline)} actions")

    def _update_component_signature(
        self,
        recognition_id: str,
        component: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Update component visual signature (neural embedding)."""
        comp_type = component.get("type", "unknown")
        confidence = component.get("confidence", 0.0)

        # Create neural embedding for component appearance
        embedding = NeuralEmbedding(
            entity_id=f"comp_sig_{comp_type}_{recognition_id}",
            entity_type=EntityType.MATERIAL,
            embedding_vector=[confidence],  # Simplified
            confidence=confidence,
            learned_from=[recognition_id],
        )

        node = KnowledgeNode(
            node_id=f"comp_{comp_type}",
            entity_type=EntityType.MATERIAL,
            embedding=embedding,
            attributes=component,
        )

        self.kb.add_node(node)
        updates["component_signatures"].append(comp_type)

    def _update_bom_knowledge(
        self,
        recognition_id: str,
        bom_validation: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Update BOM validation accuracy knowledge."""
        match_score = bom_validation.get("match_score", 0.0)

        if match_score < 0.9:
            logger.warning(
                "vitra_insa.bom_mismatch",
                recognition_id=recognition_id,
                score=match_score,
            )

        updates["bom_accuracy"].append(f"BOM match score: {match_score:.2f}")

    def _update_quality_grading(
        self,
        recognition_id: str,
        quality_assessment: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Update quality grading patterns."""
        grade = quality_assessment.get("quality_grade", "B")

        logger.debug(
            "vitra_insa.quality_grade",
            recognition_id=recognition_id,
            grade=grade,
        )

        updates["quality_patterns"].append(f"Grade: {grade}")

    def _predict_quality_from_similar(
        self,
        similar_jobs: list[tuple[str, float]],
    ) -> float:
        """Predict quality score from similar historical jobs."""
        if not similar_jobs:
            return 0.85  # Default

        # Simple average (replace with proper model)
        total_sim = sum(sim for _, sim in similar_jobs)
        weighted_quality = sum(
            sim * self.kb.get_node(job_id).attributes.get("quality_score", 85)
            for job_id, sim in similar_jobs
        )

        return weighted_quality / total_sim if total_sim > 0 else 0.85


# ===== Factory Function =====

def create_vitra_insa_bridge(kb: INSAKnowledgeBase) -> VITRAINSABridge:
    """Create VITRA-INSA bridge with initialized knowledge base."""
    bridge = VITRAINSABridge(kb)

    logger.info("vitra_insa.bridge.created")

    return bridge
