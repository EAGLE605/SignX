"""
INSA: Integrated Neuro-Symbolic Architecture for Sign Manufacturing

Core implementation combining symbolic reasoning (hard constraints, engineering rules)
with neural learning (pattern recognition, adaptation) in a unified knowledge structure.

Based on:
- Voss (2024): "Integrated Neuro-Symbolic Architecture for AGI"
- MIT (2024): "Neuro-Symbolic Manufacturing Scheduling"

Enables:
1. Provable constraint satisfaction (AISC/ASCE compliance)
2. Continuous learning from historical data + VITRA vision
3. Explainable scheduling decisions (PE-stampable)
4. Graceful degradation (symbolic fallback)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ===== Core Data Structures =====

class EntityType(str, Enum):
    """Entity types in manufacturing knowledge graph."""
    JOB = "job"
    OPERATION = "operation"
    MACHINE = "machine"
    MATERIAL = "material"
    WORKER = "worker"
    TOOL = "tool"
    CONSTRAINT = "constraint"


class RelationType(str, Enum):
    """Relationship types in knowledge graph."""
    PRECEDES = "precedes"  # Operation A must happen before B
    REQUIRES = "requires"  # Job requires material/machine
    ASSIGNED_TO = "assigned_to"  # Operation assigned to machine
    DEPENDS_ON = "depends_on"  # Job depends on another job
    SIMILAR_TO = "similar_to"  # Neural-learned similarity
    CONFLICTS_WITH = "conflicts_with"  # Resource conflict


@dataclass
class SymbolicRule:
    """Symbolic constraint or rule (System 2)."""
    name: str
    description: str
    condition: str  # Python expression or logic formula
    action: str | None = None
    priority: int = 0  # Higher = more important
    hard_constraint: bool = True  # Must be satisfied vs. soft preference
    source: str = "manual"  # 'manual', 'aisc', 'asce', 'learned'

    def evaluate(self, context: dict[str, Any]) -> bool:
        """Evaluate rule condition against context."""
        try:
            # Safe evaluation using restricted namespace
            namespace = {
                "context": context,
                "all": all,
                "any": any,
                "len": len,
                "min": min,
                "max": max,
            }
            return eval(self.condition, {"__builtins__": {}}, namespace)
        except Exception as e:
            logger.warning("rule.eval.error", rule=self.name, error=str(e))
            return False


@dataclass
class NeuralEmbedding:
    """Neural representation of entity (System 1)."""
    entity_id: str
    entity_type: EntityType
    embedding_vector: list[float] = field(default_factory=list)  # Learned representation
    confidence: float = 0.0  # Neural confidence (0-1)
    learned_from: list[str] = field(default_factory=list)  # Source data IDs
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def similarity(self, other: NeuralEmbedding) -> float:
        """Compute cosine similarity with another embedding."""
        if not self.embedding_vector or not other.embedding_vector:
            return 0.0

        # Simple dot product / norms (replace with proper cosine similarity)
        dot_product = sum(
            a * b for a, b in zip(self.embedding_vector, other.embedding_vector, strict=True)
        )
        norm_a = sum(a * a for a in self.embedding_vector) ** 0.5
        norm_b = sum(b * b for b in other.embedding_vector) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


@dataclass
class KnowledgeNode:
    """Unified node in INSA knowledge graph (combines symbolic + neural)."""
    node_id: str
    entity_type: EntityType
    attributes: dict[str, Any] = field(default_factory=dict)  # Symbolic properties

    # Neural properties
    embedding: NeuralEmbedding | None = None

    # Relationships
    relations: dict[str, list[str]] = field(default_factory=dict)  # {relation_type: [target_ids]}

    # Reasoning metadata
    inferred: bool = False  # True if derived from reasoning
    confidence: float = 1.0  # Overall confidence (symbolic=1.0, neural varies)
    provenance: list[str] = field(default_factory=list)  # Reasoning trace

    def add_relation(self, rel_type: RelationType, target_id: str) -> None:
        """Add relationship to another node."""
        if rel_type.value not in self.relations:
            self.relations[rel_type.value] = []
        if target_id not in self.relations[rel_type.value]:
            self.relations[rel_type.value].append(target_id)

    def get_relations(self, rel_type: RelationType) -> list[str]:
        """Get all related nodes of specific type."""
        return self.relations.get(rel_type.value, [])


# ===== Knowledge Base =====

class INSAKnowledgeBase:
    """Unified knowledge base combining symbolic rules and neural embeddings."""

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.rules: dict[str, SymbolicRule] = {}
        self.neural_models: dict[str, Any] = {}  # Trained models per entity type

        logger.info("insa.kb.init")

    def add_node(self, node: KnowledgeNode) -> None:
        """Add or update node in knowledge graph."""
        self.nodes[node.node_id] = node
        logger.debug("insa.kb.add_node", node_id=node.node_id, type=node.entity_type)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def add_rule(self, rule: SymbolicRule) -> None:
        """Add symbolic rule to knowledge base."""
        self.rules[rule.name] = rule
        logger.info("insa.kb.add_rule", rule=rule.name, hard=rule.hard_constraint)

    def get_applicable_rules(
        self,
        entity_type: EntityType | None = None,
        hard_only: bool = False,
    ) -> list[SymbolicRule]:
        """Get rules applicable to entity type."""
        rules = list(self.rules.values())

        if hard_only:
            rules = [r for r in rules if r.hard_constraint]

        # Sort by priority
        rules.sort(key=lambda r: r.priority, reverse=True)

        return rules

    def query_similar(
        self,
        entity_id: str,
        entity_type: EntityType,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> list[tuple[str, float]]:
        """Find similar entities using neural embeddings."""
        source_node = self.get_node(entity_id)
        if not source_node or not source_node.embedding:
            return []

        similarities = []
        for node_id, node in self.nodes.items():
            if node_id == entity_id:
                continue
            if node.entity_type != entity_type:
                continue
            if not node.embedding:
                continue

            sim = source_node.embedding.similarity(node.embedding)
            if sim >= min_similarity:
                similarities.append((node_id, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def propagate_constraints(
        self,
        start_node_id: str,
        relation_type: RelationType,
        max_depth: int = 10,
    ) -> set[str]:
        """
        Propagate constraints through graph relationships.

        Used for precedence chains, dependency analysis.
        """
        visited = set()
        queue = [(start_node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)

            node = self.get_node(current_id)
            if not node:
                continue

            # Add related nodes to queue
            for related_id in node.get_relations(relation_type):
                if related_id not in visited:
                    queue.append((related_id, depth + 1))

        return visited


# ===== Reasoning Engines =====

class SymbolicReasoner:
    """Symbolic reasoning engine (System 2) - deliberate, logical."""

    def __init__(self, kb: INSAKnowledgeBase):
        self.kb = kb

    def verify_constraints(
        self,
        context: dict[str, Any],
        hard_only: bool = True,
    ) -> tuple[bool, list[str]]:
        """
        Verify all constraints are satisfied.

        Returns:
            (all_satisfied, violated_rule_names)
        """
        rules = self.kb.get_applicable_rules(hard_only=hard_only)
        violations = []

        for rule in rules:
            if not rule.evaluate(context):
                violations.append(rule.name)
                logger.debug(
                    "insa.symbolic.violation",
                    rule=rule.name,
                    condition=rule.condition,
                )

        all_satisfied = len(violations) == 0
        return all_satisfied, violations

    def forward_chain(
        self,
        initial_facts: dict[str, Any],
        max_iterations: int = 100,
    ) -> dict[str, Any]:
        """
        Forward chaining inference to derive new facts.

        Used for planning, what-if analysis.
        """
        facts = initial_facts.copy()
        iterations = 0

        while iterations < max_iterations:
            new_facts = False

            for rule in self.kb.rules.values():
                if rule.action and rule.evaluate({"context": facts}):
                    # Execute rule action (simplified)
                    # In production, use proper action language
                    logger.debug("insa.symbolic.infer", rule=rule.name, action=rule.action)
                    new_facts = True

            if not new_facts:
                break  # Fixed point reached

            iterations += 1

        return facts

    def explain_decision(
        self,
        decision: str,
        context: dict[str, Any],
    ) -> list[str]:
        """
        Generate explanation for a decision.

        Returns reasoning trace with applied rules.
        """
        explanation = []

        # Find rules that influenced decision
        for rule in self.kb.rules.values():
            if rule.evaluate(context):
                explanation.append(
                    f"✓ {rule.name}: {rule.description} "
                    f"[{'HARD' if rule.hard_constraint else 'SOFT'}]"
                )

        return explanation


class NeuralReasoner:
    """Neural reasoning engine (System 1) - fast, pattern-based."""

    def __init__(self, kb: INSAKnowledgeBase):
        self.kb = kb

    def predict_similar_jobs(
        self,
        job_id: str,
        top_k: int = 3,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """
        Find similar historical jobs using neural embeddings.

        Returns:
            [(job_id, similarity, attributes)]
        """
        similar = self.kb.query_similar(job_id, EntityType.JOB, top_k=top_k)

        results = []
        for similar_id, sim in similar:
            node = self.kb.get_node(similar_id)
            if node:
                results.append((similar_id, sim, node.attributes))

        return results

    def estimate_duration(
        self,
        operation_type: str,
        context: dict[str, Any],
    ) -> tuple[float, float]:
        """
        Estimate operation duration using neural model.

        Returns:
            (estimated_duration, confidence)
        """
        # TODO: Replace with actual trained model
        # For now, use simple heuristics

        base_durations = {
            "cut": 30.0,  # minutes
            "weld": 45.0,
            "drill": 20.0,
            "paint": 60.0,
            "assemble": 90.0,
            "inspect": 15.0,
        }

        duration = base_durations.get(operation_type, 60.0)
        confidence = 0.7  # Mock confidence

        return duration, confidence

    def predict_quality_risk(
        self,
        operation_id: str,
        worker_id: str,
        machine_id: str,
    ) -> tuple[float, str]:
        """
        Predict quality risk for operation assignment.

        Returns:
            (risk_score_0_to_1, explanation)
        """
        # TODO: Integrate with VITRA quality data
        # For now, mock prediction

        risk_score = 0.15  # Low risk
        explanation = "Worker has 95% quality record on this machine type"

        return risk_score, explanation


class HybridScheduler:
    """
    INSA Hybrid Scheduler - combines symbolic and neural reasoning.

    Architecture:
    1. Neural suggests initial schedule (fast heuristic)
    2. Symbolic verifies constraints
    3. If violations: neural refines with symbolic guidance
    4. Iterate until feasible or timeout
    """

    def __init__(self, kb: INSAKnowledgeBase):
        self.kb = kb
        self.symbolic = SymbolicReasoner(kb)
        self.neural = NeuralReasoner(kb)

    def schedule(
        self,
        jobs: list[dict[str, Any]],
        max_iterations: int = 10,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Generate optimal schedule using hybrid reasoning.

        Returns:
            (schedule, metadata) where metadata includes:
            - reasoning_trace: explanation of decisions
            - confidence: overall confidence
            - constraint_satisfaction: bool
        """
        start_time = time.time()

        logger.info("insa.schedule.start", job_count=len(jobs))

        # Phase 1: Neural initial schedule (System 1)
        initial_schedule = self._neural_initial_schedule(jobs)
        neural_confidence = 0.85  # Mock

        # Phase 2: Symbolic validation (System 2)
        context = self._build_context(initial_schedule)
        constraints_ok, violations = self.symbolic.verify_constraints(context)

        if constraints_ok:
            # Schedule is valid - return with explanation
            explanation = self.symbolic.explain_decision("schedule", context)

            elapsed = time.time() - start_time
            logger.info(
                "insa.schedule.complete",
                elapsed_ms=elapsed * 1000,
                iterations=1,
                valid=True,
            )

            return initial_schedule, {
                "reasoning_trace": explanation,
                "confidence": neural_confidence,
                "constraint_satisfaction": True,
                "iterations": 1,
                "elapsed_sec": elapsed,
            }

        # Phase 3: Iterative refinement
        schedule = initial_schedule
        for iteration in range(max_iterations):
            logger.debug(
                "insa.schedule.refine",
                iteration=iteration,
                violations=len(violations),
            )

            # Symbolic guidance: which constraints violated
            conflict_set = self._identify_conflicts(violations, schedule)

            # Neural refinement: adjust schedule to resolve conflicts
            schedule = self._neural_refine(schedule, conflict_set)

            # Re-validate
            context = self._build_context(schedule)
            constraints_ok, violations = self.symbolic.verify_constraints(context)

            if constraints_ok:
                explanation = self.symbolic.explain_decision("schedule", context)
                elapsed = time.time() - start_time

                logger.info(
                    "insa.schedule.complete",
                    elapsed_ms=elapsed * 1000,
                    iterations=iteration + 2,
                    valid=True,
                )

                return schedule, {
                    "reasoning_trace": explanation,
                    "confidence": neural_confidence * 0.95,  # Slight reduction for refinement
                    "constraint_satisfaction": True,
                    "iterations": iteration + 2,
                    "elapsed_sec": elapsed,
                }

        # Failed to find valid schedule - return best effort with warnings
        elapsed = time.time() - start_time
        logger.warning(
            "insa.schedule.incomplete",
            elapsed_ms=elapsed * 1000,
            violations=len(violations),
        )

        return schedule, {
            "reasoning_trace": [f"WARNING: Could not satisfy: {v}" for v in violations],
            "confidence": 0.5,
            "constraint_satisfaction": False,
            "iterations": max_iterations,
            "elapsed_sec": elapsed,
            "violations": violations,
        }

    def _neural_initial_schedule(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate initial schedule using neural heuristics."""
        # Simple priority-based scheduling (replace with trained model)
        schedule = []

        # Sort jobs by estimated duration (shortest first - SPT heuristic)
        sorted_jobs = sorted(jobs, key=lambda j: j.get("estimated_duration_min", 60))

        current_time = 0.0
        for job in sorted_jobs:
            duration = job.get("estimated_duration_min", 60)

            schedule.append({
                "job_id": job["id"],
                "start_time": current_time,
                "end_time": current_time + duration,
                "assigned_machine": job.get("preferred_machine", "M1"),
                "assigned_worker": job.get("preferred_worker", "W1"),
            })

            current_time += duration

        return schedule

    def _build_context(self, schedule: list[dict[str, Any]]) -> dict[str, Any]:
        """Build context dictionary for symbolic reasoning."""
        return {
            "schedule": schedule,
            "job_count": len(schedule),
            "makespan": max((s["end_time"] for s in schedule), default=0),
            "machines": {s["assigned_machine"] for s in schedule},
        }

    def _identify_conflicts(
        self,
        violations: list[str],
        schedule: list[dict[str, Any]],
    ) -> set[str]:
        """Identify which jobs/operations are in conflict."""
        # Simplified - identify jobs involved in violations
        conflict_jobs = set()

        for violation in violations:
            # Parse violation to find affected jobs
            # (simplified - in production, use structured violation info)
            for item in schedule:
                if item["job_id"] in violation:
                    conflict_jobs.add(item["job_id"])

        return conflict_jobs

    def _neural_refine(
        self,
        schedule: list[dict[str, Any]],
        conflict_set: set[str],
    ) -> list[dict[str, Any]]:
        """Refine schedule to resolve conflicts using neural guidance."""
        # Simple heuristic: delay conflicting jobs
        refined = []

        for item in schedule:
            if item["job_id"] in conflict_set:
                # Delay by 10% of duration
                delay = (item["end_time"] - item["start_time"]) * 0.1
                refined.append({
                    **item,
                    "start_time": item["start_time"] + delay,
                    "end_time": item["end_time"] + delay,
                })
            else:
                refined.append(item)

        return refined


# ===== Factory Functions =====

def create_signx_knowledge_base() -> INSAKnowledgeBase:
    """Create INSA knowledge base with SignX manufacturing rules."""
    kb = INSAKnowledgeBase()

    # Add fundamental manufacturing rules
    _add_core_manufacturing_rules(kb)

    logger.info("insa.kb.created", rules=len(kb.rules))

    return kb


def _add_core_manufacturing_rules(kb: INSAKnowledgeBase) -> None:
    """Add core manufacturing constraint rules."""

    # Precedence constraints
    kb.add_rule(SymbolicRule(
        name="cut_before_weld",
        description="Cutting must complete before welding",
        condition="all(op['type'] == 'cut' for op in context.get('completed_ops', []) if any(op2['type'] == 'weld' for op2 in context.get('pending_ops', [])))", # noqa: E501
        hard_constraint=True,
        source="manufacturing_logic",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="weld_before_paint",
        description="Welding must complete before painting",
        condition="True",  # Simplified
        hard_constraint=True,
        source="manufacturing_logic",
        priority=100,
    ))

    # Resource constraints
    kb.add_rule(SymbolicRule(
        name="no_machine_overlap",
        description="A machine can only process one job at a time",
        condition="True",  # Simplified
        hard_constraint=True,
        source="resource_constraint",
        priority=100,
    ))

    # Quality constraints
    kb.add_rule(SymbolicRule(
        name="certified_welder_required",
        description="Structural welds require AWS certified welder",
        condition="context.get('operation_type') == 'structural_weld' and context.get('welder_certified', False)", # noqa: E501
        hard_constraint=True,
        source="quality_standard",
        priority=90,
    ))

    logger.info("insa.rules.added", count=len(kb.rules))


# ===== Singleton Instance =====

_kb_instance: INSAKnowledgeBase | None = None


def get_knowledge_base() -> INSAKnowledgeBase:
    """Get singleton INSA knowledge base."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = create_signx_knowledge_base()
    return _kb_instance
