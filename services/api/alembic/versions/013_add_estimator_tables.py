"""Add estimator tables for quotes, BOM, and labor takeoff.

Revision ID: 013
Revises: 012
Create Date: 2025-12-11

Tables:
- estimates: Main estimate header with customer/project info and rollup totals
- labor_line_items: Labor breakdown with work codes and hours
- material_line_items: Material BOM with part numbers and quantities
- subcontractor_items: Subcontractor quotes
- permit_items: Permit fees
- work_codes: Standard labor work code catalog
- material_catalog: Material master with pricing
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("""
        CREATE TYPE estimate_status AS ENUM (
            'draft', 'pending', 'sent', 'accepted', 'rejected', 'cancelled', 'invoiced'
        )
    """)
    op.execute("""
        CREATE TYPE labor_category AS ENUM (
            'fabrication', 'engineering', 'installation', 'electrical', 'graphics', 'project_management', 'service'
        )
    """)
    op.execute("""
        CREATE TYPE material_category AS ENUM (
            'aluminum', 'steel', 'acrylic', 'electrical', 'vinyl', 'fasteners', 'concrete', 'paint', 'channel_letters', 'miscellaneous'
        )
    """)
    op.execute("""
        CREATE TYPE unit_of_measure AS ENUM (
            'each', 'linear_ft', 'sq_ft', 'cubic_yard', 'lb', 'gallon', 'sheet', 'roll', 'box', 'set'
        )
    """)

    # ============================================================
    # Work Codes Catalog
    # ============================================================
    op.create_table(
        'work_codes',
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('category', postgresql.ENUM('fabrication', 'engineering', 'installation', 'electrical', 'graphics', 'project_management', 'service', name='labor_category', create_type=False), nullable=False),
        sa.Column('default_rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('typical_hours', sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('code'),
    )
    op.create_index('ix_work_codes_category', 'work_codes', ['category'])
    op.create_index('ix_work_codes_is_active', 'work_codes', ['is_active'])

    # ============================================================
    # Material Catalog
    # ============================================================
    op.create_table(
        'material_catalog',
        sa.Column('part_number', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('category', postgresql.ENUM('aluminum', 'steel', 'acrylic', 'electrical', 'vinyl', 'fasteners', 'concrete', 'paint', 'channel_letters', 'miscellaneous', name='material_category', create_type=False), nullable=False),
        sa.Column('unit', postgresql.ENUM('each', 'linear_ft', 'sq_ft', 'cubic_yard', 'lb', 'gallon', 'sheet', 'roll', 'box', 'set', name='unit_of_measure', create_type=False), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('last_cost_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('preferred_vendor', sa.String(length=200), nullable=True),
        sa.Column('vendor_part_number', sa.String(length=100), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_taxable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('keyedin_item_id', sa.String(length=100), nullable=True),
        sa.Column('keyedin_price_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('part_number'),
    )
    op.create_index('ix_material_catalog_category', 'material_catalog', ['category'])
    op.create_index('ix_material_catalog_is_active', 'material_catalog', ['is_active'])
    op.create_index('ix_material_catalog_vendor', 'material_catalog', ['preferred_vendor'])
    op.create_index('ix_material_catalog_description', 'material_catalog', ['description'], postgresql_using='gin', postgresql_ops={'description': 'gin_trgm_ops'})

    # ============================================================
    # Estimates (Main Table)
    # ============================================================
    op.create_table(
        'estimates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estimate_number', sa.String(length=50), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'pending', 'sent', 'accepted', 'rejected', 'cancelled', 'invoiced', name='estimate_status', create_type=False), server_default='draft', nullable=False),

        # Customer Info
        sa.Column('customer_name', sa.String(length=200), nullable=False),
        sa.Column('customer_email', sa.String(length=200), nullable=True),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('customer_company', sa.String(length=200), nullable=True),

        # Project Info
        sa.Column('project_name', sa.String(length=200), nullable=False),
        sa.Column('job_site_address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),

        # Sign Specifications (JSON)
        sa.Column('sign_specs', postgresql.JSON(astext_type=sa.Text()), nullable=True),

        # Engineering
        sa.Column('wind_speed_mph', sa.Numeric(precision=5, scale=1), nullable=True),
        sa.Column('exposure_category', sa.String(length=1), nullable=True),

        # Markup Percentages
        sa.Column('labor_burden_percent', sa.Numeric(precision=5, scale=2), server_default='25.00', nullable=False),
        sa.Column('materials_tax_percent', sa.Numeric(precision=5, scale=2), server_default='7.00', nullable=False),
        sa.Column('materials_freight', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('overhead_percent', sa.Numeric(precision=5, scale=2), server_default='15.00', nullable=False),
        sa.Column('profit_percent', sa.Numeric(precision=5, scale=2), server_default='20.00', nullable=False),

        # Computed Totals (updated on recalculate)
        sa.Column('labor_hours', sa.Numeric(precision=8, scale=2), server_default='0.00', nullable=False),
        sa.Column('labor_subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('labor_burden_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('labor_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),

        sa.Column('materials_subtotal', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('materials_tax_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('materials_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),

        sa.Column('subcontractors_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('permits_total', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),

        sa.Column('direct_cost', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('overhead_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('profit_amount', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),

        sa.Column('sell_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('quoted_price', sa.Numeric(precision=12, scale=2), server_default='0.00', nullable=False),
        sa.Column('gross_margin_percent', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),

        # Validity
        sa.Column('valid_days', sa.Integer(), server_default='30', nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),

        # Notes
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('customer_notes', sa.Text(), nullable=True),
        sa.Column('terms_conditions', sa.Text(), nullable=True),

        # KeyedIn Integration
        sa.Column('keyedin_quote_id', sa.String(length=100), nullable=True),
        sa.Column('keyedin_synced_at', sa.DateTime(timezone=True), nullable=True),

        # Audit
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('estimate_number'),
    )
    op.create_index('ix_estimates_estimate_number', 'estimates', ['estimate_number'])
    op.create_index('ix_estimates_status', 'estimates', ['status'])
    op.create_index('ix_estimates_customer_name', 'estimates', ['customer_name'])
    op.create_index('ix_estimates_project_id', 'estimates', ['project_id'])
    op.create_index('ix_estimates_created_at', 'estimates', ['created_at'])
    op.create_index('ix_estimates_keyedin_quote_id', 'estimates', ['keyedin_quote_id'])

    # ============================================================
    # Labor Line Items
    # ============================================================
    op.create_table(
        'labor_line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estimate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('work_code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('category', postgresql.ENUM('fabrication', 'engineering', 'installation', 'electrical', 'graphics', 'project_management', 'service', name='labor_category', create_type=False), nullable=False),
        sa.Column('hours', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('rate', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('extended', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_labor_line_items_estimate_id', 'labor_line_items', ['estimate_id'])
    op.create_index('ix_labor_line_items_work_code', 'labor_line_items', ['work_code'])
    op.create_index('ix_labor_line_items_category', 'labor_line_items', ['category'])

    # ============================================================
    # Material Line Items
    # ============================================================
    op.create_table(
        'material_line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estimate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('part_number', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('category', postgresql.ENUM('aluminum', 'steel', 'acrylic', 'electrical', 'vinyl', 'fasteners', 'concrete', 'paint', 'channel_letters', 'miscellaneous', name='material_category', create_type=False), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('unit', postgresql.ENUM('each', 'linear_ft', 'sq_ft', 'cubic_yard', 'lb', 'gallon', 'sheet', 'roll', 'box', 'set', name='unit_of_measure', create_type=False), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('extended', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('vendor', sa.String(length=200), nullable=True),
        sa.Column('vendor_part_number', sa.String(length=100), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_taxable', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('keyedin_item_id', sa.String(length=100), nullable=True),
        sa.Column('keyedin_price_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_material_line_items_estimate_id', 'material_line_items', ['estimate_id'])
    op.create_index('ix_material_line_items_part_number', 'material_line_items', ['part_number'])
    op.create_index('ix_material_line_items_category', 'material_line_items', ['category'])

    # ============================================================
    # Subcontractor Items
    # ============================================================
    op.create_table(
        'subcontractor_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estimate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vendor_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('trade', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('quote_number', sa.String(length=100), nullable=True),
        sa.Column('quote_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subcontractor_items_estimate_id', 'subcontractor_items', ['estimate_id'])
    op.create_index('ix_subcontractor_items_trade', 'subcontractor_items', ['trade'])

    # ============================================================
    # Permit Items
    # ============================================================
    op.create_table(
        'permit_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estimate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permit_type', sa.String(length=100), nullable=False),
        sa.Column('jurisdiction', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('permit_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['estimate_id'], ['estimates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_permit_items_estimate_id', 'permit_items', ['estimate_id'])
    op.create_index('ix_permit_items_permit_type', 'permit_items', ['permit_type'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_permit_items_permit_type', table_name='permit_items')
    op.drop_index('ix_permit_items_estimate_id', table_name='permit_items')
    op.drop_table('permit_items')

    op.drop_index('ix_subcontractor_items_trade', table_name='subcontractor_items')
    op.drop_index('ix_subcontractor_items_estimate_id', table_name='subcontractor_items')
    op.drop_table('subcontractor_items')

    op.drop_index('ix_material_line_items_category', table_name='material_line_items')
    op.drop_index('ix_material_line_items_part_number', table_name='material_line_items')
    op.drop_index('ix_material_line_items_estimate_id', table_name='material_line_items')
    op.drop_table('material_line_items')

    op.drop_index('ix_labor_line_items_category', table_name='labor_line_items')
    op.drop_index('ix_labor_line_items_work_code', table_name='labor_line_items')
    op.drop_index('ix_labor_line_items_estimate_id', table_name='labor_line_items')
    op.drop_table('labor_line_items')

    op.drop_index('ix_estimates_keyedin_quote_id', table_name='estimates')
    op.drop_index('ix_estimates_created_at', table_name='estimates')
    op.drop_index('ix_estimates_project_id', table_name='estimates')
    op.drop_index('ix_estimates_customer_name', table_name='estimates')
    op.drop_index('ix_estimates_status', table_name='estimates')
    op.drop_index('ix_estimates_estimate_number', table_name='estimates')
    op.drop_table('estimates')

    op.drop_index('ix_material_catalog_description', table_name='material_catalog')
    op.drop_index('ix_material_catalog_vendor', table_name='material_catalog')
    op.drop_index('ix_material_catalog_is_active', table_name='material_catalog')
    op.drop_index('ix_material_catalog_category', table_name='material_catalog')
    op.drop_table('material_catalog')

    op.drop_index('ix_work_codes_is_active', table_name='work_codes')
    op.drop_index('ix_work_codes_category', table_name='work_codes')
    op.drop_table('work_codes')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS unit_of_measure")
    op.execute("DROP TYPE IF EXISTS material_category")
    op.execute("DROP TYPE IF EXISTS labor_category")
    op.execute("DROP TYPE IF EXISTS estimate_status")
