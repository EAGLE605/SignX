"""INSA Symbolic Rules for Sign Manufacturing.

Encodes engineering standards, manufacturing constraints, and domain knowledge
as symbolic rules for the INSA reasoning engine.

Standards covered:
- AISC 360-22: Steel Construction Manual
- ASCE 7-22: Minimum Design Loads and Associated Criteria
- AWS D1.1: Structural Welding Code - Steel
- IBC 2024: International Building Code
- Manufacturing best practices
"""

from __future__ import annotations

from insa_core import INSAKnowledgeBase, SymbolicRule


def add_aisc_rules(kb: INSAKnowledgeBase) -> None:
    """Add AISC 360-22 structural steel design rules."""
    # ===== Base Plate Design (AISC 360-22 Chapter J) =====

    kb.add_rule(SymbolicRule(
        name="aisc_baseplate_min_thickness",
        description="AISC 360-22: Base plate thickness ≥ 0.25 inches for structural applications",
        condition="context.get('plate_thickness_in', 0) >= 0.25",
        hard_constraint=True,
        source="aisc_360_22",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_baseplate_steel_grade",
        description="AISC 360-22: Base plate must be ASTM A36 or higher grade steel",
        condition="context.get('plate_material', '') in ['A36', 'A572', 'A992', 'A500']",
        hard_constraint=True,
        source="aisc_360_22",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_anchor_bolt_embedment",
        description="AISC 360-22: Anchor bolt embedment ≥ 7 × bolt diameter",
        condition="context.get('anchor_embed_in', 0) >= 7 * context.get('anchor_dia_in', 0.75)",
        hard_constraint=True,
        source="aisc_360_22",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_weld_min_size",
        description="AISC 360-22 Table J2.4: Minimum fillet weld size based on material thickness",
        condition=(
            "(context.get('material_thickness_in', 0) <= 0.25 and context.get('weld_size_in', 0) >= 0.125) or " # noqa: E501
            "(context.get('material_thickness_in', 0) <= 0.5 and context.get('weld_size_in', 0) >= 0.1875) or " # noqa: E501
            "(context.get('material_thickness_in', 0) <= 0.75 and context.get('weld_size_in', 0) >= 0.25) or " # noqa: E501
            "(context.get('weld_size_in', 0) >= 0.3125)"
        ),
        hard_constraint=True,
        source="aisc_360_22_table_j2_4",
        priority=95,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_weld_max_size",
        description="AISC 360-22 J2.2b: Maximum fillet weld size ≤ material thickness",
        condition="context.get('weld_size_in', 0) <= context.get('material_thickness_in', 1.0)",
        hard_constraint=True,
        source="aisc_360_22",
        priority=95,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_hss_minimum_thickness",
        description="AISC 360-22: HSS pole wall thickness ≥ 0.125 inches for structural use",
        condition="context.get('hss_wall_thickness_in', 0) >= 0.125",
        hard_constraint=True,
        source="aisc_360_22",
        priority=90,
    ))

    # ===== Connection Design =====

    kb.add_rule(SymbolicRule(
        name="aisc_bolt_spacing_minimum",
        description="AISC 360-22 J3.3: Minimum bolt spacing = 2.67 × bolt diameter",
        condition="context.get('bolt_spacing_in', 0) >= 2.67 * context.get('bolt_dia_in', 0.75)",
        hard_constraint=True,
        source="aisc_360_22_j3_3",
        priority=90,
    ))

    kb.add_rule(SymbolicRule(
        name="aisc_edge_distance_minimum",
        description="AISC 360-22 J3.4: Minimum edge distance = 1.5 × bolt diameter",
        condition="context.get('edge_distance_in', 0) >= 1.5 * context.get('bolt_dia_in', 0.75)",
        hard_constraint=True,
        source="aisc_360_22_j3_4",
        priority=90,
    ))


def add_asce_rules(kb: INSAKnowledgeBase) -> None:
    """Add ASCE 7-22 wind and seismic load rules."""
    # ===== Wind Load Requirements =====

    kb.add_rule(SymbolicRule(
        name="asce7_basic_wind_speed",
        description="ASCE 7-22: Basic wind speed ≥ 115 mph for Risk Category II signs",
        condition="context.get('wind_speed_mph', 0) >= 115",
        hard_constraint=True,
        source="asce_7_22_fig_26_5_1",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="asce7_exposure_category",
        description="ASCE 7-22: Exposure category must be B, C, or D",
        condition="context.get('exposure_category', '') in ['B', 'C', 'D']",
        hard_constraint=True,
        source="asce_7_22_sec_26_7",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="asce7_importance_factor",
        description="ASCE 7-22: Importance factor I ≥ 1.0 for all risk categories",
        condition="context.get('importance_factor', 0) >= 1.0",
        hard_constraint=True,
        source="asce_7_22_table_26_11_1",
        priority=95,
    ))

    kb.add_rule(SymbolicRule(
        name="asce7_gust_effect_factor",
        description="ASCE 7-22: Gust effect factor G typically 0.85 for rigid structures",
        condition="0.8 <= context.get('gust_factor', 0.85) <= 1.0",
        hard_constraint=False,  # Soft recommendation
        source="asce_7_22_sec_26_11",
        priority=50,
    ))

    # ===== Seismic Requirements =====

    kb.add_rule(SymbolicRule(
        name="asce7_seismic_design_category",
        description="ASCE 7-22: Seismic Design Category must be A through F",
        condition="context.get('seismic_category', '') in ['A', 'B', 'C', 'D', 'E', 'F']",
        hard_constraint=True,
        source="asce_7_22_sec_11_6",
        priority=90,
    ))

    kb.add_rule(SymbolicRule(
        name="asce7_seismic_importance_factor",
        description="ASCE 7-22: Seismic importance factor Ie ≥ 1.0",
        condition="context.get('seismic_ie', 0) >= 1.0",
        hard_constraint=True,
        source="asce_7_22_table_1_5_2",
        priority=90,
    ))


def add_aws_welding_rules(kb: INSAKnowledgeBase) -> None:
    """Add AWS D1.1 structural welding code rules."""
    kb.add_rule(SymbolicRule(
        name="aws_welder_certification_required",
        description="AWS D1.1: Welders must be certified for structural welding",
        condition="context.get('welder_certified', False) == True",
        hard_constraint=True,
        source="aws_d1_1",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="aws_weld_prequalified",
        description="AWS D1.1: Use prequalified joint details when possible",
        condition="context.get('joint_type', '') in ['square_groove', 'single_v', 'double_v', 'single_bevel', 'fillet']", # noqa: E501
        hard_constraint=False,  # Preference
        source="aws_d1_1_sec_3",
        priority=60,
    ))

    kb.add_rule(SymbolicRule(
        name="aws_base_metal_cleanliness",
        description="AWS D1.1: Base metal must be free of rust, mill scale, and coatings at weld location", # noqa: E501
        condition="context.get('surface_prepared', False) == True",
        hard_constraint=True,
        source="aws_d1_1_sec_5_14",
        priority=90,
    ))

    kb.add_rule(SymbolicRule(
        name="aws_weld_inspection_required",
        description="AWS D1.1: Visual inspection required for all structural welds",
        condition="context.get('inspection_planned', True) == True",
        hard_constraint=True,
        source="aws_d1_1_sec_6",
        priority=85,
    ))

    kb.add_rule(SymbolicRule(
        name="aws_preheat_low_temp",
        description="AWS D1.1: Preheat required if ambient temperature < 32°F",
        condition=(
            "context.get('ambient_temp_f', 70) >= 32 or "
            "context.get('preheat_applied', False) == True"
        ),
        hard_constraint=True,
        source="aws_d1_1_table_3_2",
        priority=80,
    ))


def add_ibc_rules(kb: INSAKnowledgeBase) -> None:
    """Add IBC 2024 building code rules for sign structures."""
    kb.add_rule(SymbolicRule(
        name="ibc_permit_required",
        description="IBC 2024: Building permit required for permanent signs",
        condition="context.get('permit_status', '') in ['approved', 'submitted']",
        hard_constraint=True,
        source="ibc_2024_sec_105",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="ibc_foundation_depth_frost",
        description="IBC 2024: Foundation must extend below frost depth",
        condition="context.get('foundation_depth_ft', 0) >= context.get('frost_depth_ft', 3.5)",
        hard_constraint=True,
        source="ibc_2024_sec_1809_5",
        priority=95,
    ))

    kb.add_rule(SymbolicRule(
        name="ibc_setback_requirement",
        description="IBC 2024: Sign setback from property line ≥ 10 ft for freestanding signs",
        condition="context.get('setback_ft', 0) >= 10 or context.get('sign_type', '') != 'freestanding'", # noqa: E501
        hard_constraint=True,
        source="ibc_2024_local_amendments",
        priority=85,
    ))

    kb.add_rule(SymbolicRule(
        name="ibc_height_restriction",
        description="IBC 2024: Maximum sign height 35 ft without special engineering (typical)",
        condition="context.get('sign_height_ft', 0) <= 35 or context.get('pe_stamped', False) == True", # noqa: E501
        hard_constraint=False,  # Varies by jurisdiction
        source="ibc_2024_local_amendments",
        priority=70,
    ))


def add_manufacturing_rules(kb: INSAKnowledgeBase) -> None:
    """Add manufacturing process and sequencing rules."""
    # ===== Process Sequencing =====

    kb.add_rule(SymbolicRule(
        name="mfg_cut_before_weld",
        description="Manufacturing: All cutting must complete before welding operations",
        condition=(
            "all(op.get('status') == 'completed' for op in context.get('operations', []) if op.get('type') == 'cut') or " # noqa: E501
            "not any(op.get('type') == 'weld' for op in context.get('operations', []))"
        ),
        hard_constraint=True,
        source="manufacturing_logic",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_weld_before_paint",
        description="Manufacturing: Welding must complete before painting/coating",
        condition=(
            "all(op.get('status') == 'completed' for op in context.get('operations', []) if op.get('type') == 'weld') or " # noqa: E501
            "not any(op.get('type') == 'paint' for op in context.get('operations', []))"
        ),
        hard_constraint=True,
        source="manufacturing_logic",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_fabricate_before_install",
        description="Manufacturing: All fabrication must complete before installation",
        condition=(
            "context.get('fabrication_complete', False) == True or "
            "context.get('phase', '') != 'installation'"
        ),
        hard_constraint=True,
        source="manufacturing_logic",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_inspection_before_shipment",
        description="Manufacturing: Quality inspection required before shipment",
        condition=(
            "context.get('inspection_passed', False) == True or "
            "context.get('phase', '') not in ['shipping', 'installation']"
        ),
        hard_constraint=True,
        source="quality_control",
        priority=95,
    ))

    # ===== Resource Constraints =====

    kb.add_rule(SymbolicRule(
        name="mfg_no_machine_overlap",
        description="Manufacturing: Machine can only process one operation at a time",
        condition="True",  # Enforced by scheduler logic
        hard_constraint=True,
        source="resource_constraint",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_crane_availability",
        description="Manufacturing: Heavy lifts require crane availability (> 500 lbs)",
        condition=(
            "context.get('component_weight_lbs', 0) <= 500 or "
            "context.get('crane_available', False) == True"
        ),
        hard_constraint=True,
        source="safety",
        priority=90,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_certified_operator_heavy_equipment",
        description="Manufacturing: Certified operator required for CNC, press brake, crane",
        condition=(
            "context.get('machine_type', '') not in ['cnc', 'press_brake', 'crane'] or "
            "context.get('operator_certified', False) == True"
        ),
        hard_constraint=True,
        source="safety",
        priority=90,
    ))

    # ===== Quality Control =====

    kb.add_rule(SymbolicRule(
        name="mfg_weld_cooling_time",
        description="Manufacturing: Allow 30 min cooling time for structural welds before handling",
        condition=(
            "context.get('time_since_weld_min', 999) >= 30 or "
            "context.get('operation_type', '') != 'weld'"
        ),
        hard_constraint=False,  # Best practice
        source="best_practice",
        priority=60,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_dimensional_tolerance",
        description="Manufacturing: Final dimensions must be within ±1/8 inch tolerance",
        condition="abs(context.get('actual_dimension_in', 0) - context.get('nominal_dimension_in', 0)) <= 0.125", # noqa: E501
        hard_constraint=True,
        source="tolerance_spec",
        priority=85,
    ))

    # ===== Material Handling =====

    kb.add_rule(SymbolicRule(
        name="mfg_material_availability",
        description="Manufacturing: Raw materials must be available before scheduling fabrication",
        condition="context.get('materials_in_stock', False) == True",
        hard_constraint=True,
        source="inventory",
        priority=95,
    ))

    kb.add_rule(SymbolicRule(
        name="mfg_hss_length_limit",
        description="Manufacturing: Standard HSS stock length 20-24 ft (minimize waste)",
        condition=(
            "context.get('hss_length_ft', 0) <= 24 or "
            "context.get('custom_order_approved', False) == True"
        ),
        hard_constraint=False,  # Economic optimization
        source="procurement",
        priority=40,
    ))


def add_vitra_integration_rules(kb: INSAKnowledgeBase) -> None:
    """Add rules for VITRA vision AI integration."""
    kb.add_rule(SymbolicRule(
        name="vitra_quality_threshold",
        description="VITRA: Component must pass quality inspection (score ≥ 85/100)",
        condition="context.get('vitra_quality_score', 100) >= 85",
        hard_constraint=True,
        source="vitra_quality",
        priority=90,
    ))

    kb.add_rule(SymbolicRule(
        name="vitra_safety_violation_halt",
        description="VITRA: Critical safety violations halt production immediately",
        condition=(
            "not any(v.get('severity') == 'critical' for v in context.get('vitra_safety_violations', []))" # noqa: E501
        ),
        hard_constraint=True,
        source="vitra_safety",
        priority=100,
    ))

    kb.add_rule(SymbolicRule(
        name="vitra_component_recognition_confidence",
        description="VITRA: Component recognition confidence ≥ 0.9 for automated BOM validation",
        condition=(
            "context.get('vitra_recognition_confidence', 1.0) >= 0.9 or "
            "context.get('manual_verification', False) == True"
        ),
        hard_constraint=False,  # Can fall back to manual
        source="vitra_automation",
        priority=70,
    ))

    kb.add_rule(SymbolicRule(
        name="vitra_installation_compliance",
        description="VITRA: Installation video must show ≥ 90% procedure compliance",
        condition="context.get('vitra_compliance_pct', 100) >= 90",
        hard_constraint=False,  # Quality indicator
        source="vitra_installation",
        priority=75,
    ))


def load_all_rules(kb: INSAKnowledgeBase) -> None:
    """Load all symbolic rules into knowledge base."""
    add_aisc_rules(kb)
    add_asce_rules(kb)
    add_aws_welding_rules(kb)
    add_ibc_rules(kb)
    add_manufacturing_rules(kb)
    add_vitra_integration_rules(kb)


# ===== Usage Example =====

if __name__ == "__main__":
    from insa_core import create_signx_knowledge_base

    kb = create_signx_knowledge_base()
    load_all_rules(kb)


    sources = {}
    for rule in kb.rules.values():
        sources[rule.source] = sources.get(rule.source, 0) + 1

    for _source, _count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        pass

    hard = sum(1 for r in kb.rules.values() if r.hard_constraint)
    soft = len(kb.rules) - hard
