"""Add VITRA vision analysis and robotic fabrication tables

Revision ID: 013_vitra_vision
Revises: 012_restructure_to_pole_architecture
Create Date: 2025-11-12

Adds comprehensive vision analysis capabilities:
- Sign inspection from images/video
- Installation process documentation
- Component recognition and validation
- AR-assisted design review
- Robotic fabrication support
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '013_vitra_vision'
down_revision: str | None = '012_restructure_to_pole_architecture'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add VITRA vision analysis tables."""

    # Create enums for vision analysis
    inspection_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed',
        name='inspection_status',
        create_type=True
    )
    inspection_status_enum.create(op.get_bind(), checkfirst=True)

    inspection_severity_enum = postgresql.ENUM(
        'critical', 'high', 'medium', 'low', 'informational',
        name='inspection_severity',
        create_type=True
    )
    inspection_severity_enum.create(op.get_bind(), checkfirst=True)

    component_type_enum = postgresql.ENUM(
        'pole', 'base_plate', 'anchor_bolt', 'cabinet', 'weld', 'fastener', 'foundation', 'other',
        name='component_type',
        create_type=True
    )
    component_type_enum.create(op.get_bind(), checkfirst=True)

    fabrication_task_enum = postgresql.ENUM(
        'welding', 'cutting', 'drilling', 'assembly', 'inspection', 'packaging',
        name='fabrication_task',
        create_type=True
    )
    fabrication_task_enum.create(op.get_bind(), checkfirst=True)

    # ===== 1. Vision Inspections Table (Sign Inspection) =====
    op.create_table(
        'vision_inspections',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('project_id', sa.String(64), nullable=True),
        sa.Column('sign_id', sa.String(64), nullable=True),  # Reference to installed sign
        sa.Column('inspector_id', sa.String(255), nullable=False),
        sa.Column('inspection_type', sa.String(64), nullable=False),  # 'initial', 'periodic', 'damage_assessment'
        sa.Column('status', inspection_status_enum, nullable=False, server_default='pending'),

        # Media references
        sa.Column('media_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # List of image/video URLs
        sa.Column('media_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Analysis results
        sa.Column('vitra_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('detected_issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('structural_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('safety_score', sa.Float(), nullable=True),  # 0-100
        sa.Column('maintenance_recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Geolocation
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(255), nullable=True),

        # Metadata
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    )

    # ===== 2. Inspection Issues Table =====
    op.create_table(
        'inspection_issues',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('inspection_id', sa.String(64), nullable=False),
        sa.Column('issue_type', sa.String(128), nullable=False),  # 'corrosion', 'crack', 'loose_connection', etc.
        sa.Column('severity', inspection_severity_enum, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),  # VITRA confidence 0-1

        # Location in media
        sa.Column('media_index', sa.Integer(), nullable=False),  # Which image/video frame
        sa.Column('bounding_box', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # {x, y, w, h}
        sa.Column('timestamp_sec', sa.Float(), nullable=True),  # For video

        # Issue details
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_component', component_type_enum, nullable=True),
        sa.Column('estimated_repair_cost', sa.Float(), nullable=True),
        sa.Column('priority_rank', sa.Integer(), nullable=True),

        # Resolution tracking
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['inspection_id'], ['vision_inspections.id'], ondelete='CASCADE'),
    )

    # ===== 3. Installation Videos Table (Process Documentation) =====
    op.create_table(
        'installation_videos',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('project_id', sa.String(64), nullable=False),
        sa.Column('installation_phase', sa.String(64), nullable=False),  # 'foundation', 'pole_erection', 'cabinet_mount', etc.
        sa.Column('status', inspection_status_enum, nullable=False, server_default='pending'),

        # Video metadata
        sa.Column('video_url', sa.String(512), nullable=False),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('resolution', sa.String(32), nullable=True),  # e.g., '1920x1080'
        sa.Column('uploaded_by', sa.String(255), nullable=False),

        # VITRA analysis
        sa.Column('action_timeline', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Detected actions over time
        sa.Column('procedure_compliance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('safety_violations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),  # 0-100
        sa.Column('completion_percentage', sa.Float(), nullable=True),

        # Automated report
        sa.Column('generated_report', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('report_pdf_url', sa.String(512), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # ===== 4. Component Recognition Table =====
    op.create_table(
        'component_recognitions',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('project_id', sa.String(64), nullable=True),
        sa.Column('bom_id', sa.String(64), nullable=True),  # Reference to BOM if validating against it
        sa.Column('status', inspection_status_enum, nullable=False, server_default='pending'),

        # Media
        sa.Column('image_url', sa.String(512), nullable=False),
        sa.Column('uploaded_by', sa.String(255), nullable=False),

        # Recognition results
        sa.Column('detected_components', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('material_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dimension_verification', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # BOM validation
        sa.Column('bom_match_score', sa.Float(), nullable=True),  # 0-1
        sa.Column('discrepancies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_passed', sa.Boolean(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    )

    # ===== 5. AR Design Reviews Table =====
    op.create_table(
        'ar_design_reviews',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('project_id', sa.String(64), nullable=False),
        sa.Column('reviewer_id', sa.String(255), nullable=False),

        # Site photo
        sa.Column('site_photo_url', sa.String(512), nullable=False),
        sa.Column('camera_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # Focal length, position, etc.

        # Design overlay
        sa.Column('design_overlay_url', sa.String(512), nullable=True),  # AR-rendered image
        sa.Column('design_spec', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # Sign dimensions, position

        # Analysis
        sa.Column('feasibility_score', sa.Float(), nullable=True),  # 0-100
        sa.Column('clearance_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('visual_impact_assessment', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('site_constraints', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Geolocation
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    )

    # ===== 6. Robotic Fabrication Sessions Table =====
    op.create_table(
        'robotic_fabrication_sessions',
        sa.Column('id', sa.String(64), nullable=False),
        sa.Column('project_id', sa.String(64), nullable=True),
        sa.Column('component_id', sa.String(64), nullable=True),
        sa.Column('robot_id', sa.String(128), nullable=False),
        sa.Column('task_type', fabrication_task_enum, nullable=False),
        sa.Column('status', inspection_status_enum, nullable=False, server_default='pending'),

        # Task definition
        sa.Column('task_specification', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('vla_model_version', sa.String(64), nullable=False),  # VITRA VLA model version

        # Execution
        sa.Column('action_sequence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # VLA actions
        sa.Column('video_recording_url', sa.String(512), nullable=True),
        sa.Column('sensor_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Quality control
        sa.Column('quality_checks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('defects_detected', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pass_fail_status', sa.Boolean(), nullable=True),

        # Performance metrics
        sa.Column('cycle_time_sec', sa.Float(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    )

    # Create indexes for performance
    op.create_index('ix_vision_inspections_project', 'vision_inspections', ['project_id'])
    op.create_index('ix_vision_inspections_status', 'vision_inspections', ['status'])
    op.create_index('ix_vision_inspections_created', 'vision_inspections', ['created_at'])

    op.create_index('ix_inspection_issues_inspection', 'inspection_issues', ['inspection_id'])
    op.create_index('ix_inspection_issues_severity', 'inspection_issues', ['severity'])
    op.create_index('ix_inspection_issues_resolved', 'inspection_issues', ['resolved'])

    op.create_index('ix_installation_videos_project', 'installation_videos', ['project_id'])
    op.create_index('ix_installation_videos_phase', 'installation_videos', ['installation_phase'])
    op.create_index('ix_installation_videos_status', 'installation_videos', ['status'])

    op.create_index('ix_component_recognitions_project', 'component_recognitions', ['project_id'])
    op.create_index('ix_component_recognitions_status', 'component_recognitions', ['status'])

    op.create_index('ix_ar_design_reviews_project', 'ar_design_reviews', ['project_id'])
    op.create_index('ix_ar_design_reviews_created', 'ar_design_reviews', ['created_at'])

    op.create_index('ix_robotic_sessions_project', 'robotic_fabrication_sessions', ['project_id'])
    op.create_index('ix_robotic_sessions_robot', 'robotic_fabrication_sessions', ['robot_id'])
    op.create_index('ix_robotic_sessions_status', 'robotic_fabrication_sessions', ['status'])


def downgrade() -> None:
    """Remove VITRA vision analysis tables."""

    # Drop indexes
    op.drop_index('ix_robotic_sessions_status', 'robotic_fabrication_sessions')
    op.drop_index('ix_robotic_sessions_robot', 'robotic_fabrication_sessions')
    op.drop_index('ix_robotic_sessions_project', 'robotic_fabrication_sessions')

    op.drop_index('ix_ar_design_reviews_created', 'ar_design_reviews')
    op.drop_index('ix_ar_design_reviews_project', 'ar_design_reviews')

    op.drop_index('ix_component_recognitions_status', 'component_recognitions')
    op.drop_index('ix_component_recognitions_project', 'component_recognitions')

    op.drop_index('ix_installation_videos_status', 'installation_videos')
    op.drop_index('ix_installation_videos_phase', 'installation_videos')
    op.drop_index('ix_installation_videos_project', 'installation_videos')

    op.drop_index('ix_inspection_issues_resolved', 'inspection_issues')
    op.drop_index('ix_inspection_issues_severity', 'inspection_issues')
    op.drop_index('ix_inspection_issues_inspection', 'inspection_issues')

    op.drop_index('ix_vision_inspections_created', 'vision_inspections')
    op.drop_index('ix_vision_inspections_status', 'vision_inspections')
    op.drop_index('ix_vision_inspections_project', 'vision_inspections')

    # Drop tables
    op.drop_table('robotic_fabrication_sessions')
    op.drop_table('ar_design_reviews')
    op.drop_table('component_recognitions')
    op.drop_table('installation_videos')
    op.drop_table('inspection_issues')
    op.drop_table('vision_inspections')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS fabrication_task')
    op.execute('DROP TYPE IF EXISTS component_type')
    op.execute('DROP TYPE IF EXISTS inspection_severity')
    op.execute('DROP TYPE IF EXISTS inspection_status')
