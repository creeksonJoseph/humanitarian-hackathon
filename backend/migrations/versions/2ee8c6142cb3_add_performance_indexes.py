"""add_performance_indexes

Revision ID: 2ee8c6142cb3
Revises: 
Create Date: 2026-03-09 17:50:30.828553

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ee8c6142cb3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Emergency Jobs indexes
    op.create_index('idx_emergency_jobs_status_created', 'emergency_jobs', ['status', 'created_at'])
    op.create_index('idx_emergency_jobs_village_status', 'emergency_jobs', ['village_code', 'status'])
    op.create_index('idx_emergency_jobs_assigned_rider', 'emergency_jobs', ['assigned_rider'])
    
    # Riders indexes
    op.create_index('idx_riders_status', 'riders', ['status'])
    op.create_index('idx_riders_location_status', 'riders', ['last_known_location_code', 'status'])
    op.create_index('idx_riders_verified', 'riders', ['is_verified'])
    
    # Hazard Reports indexes
    op.create_index('idx_hazards_status_expires', 'hazard_reports', ['status', 'expires_at'])
    op.create_index('idx_hazards_reported_at', 'hazard_reports', ['reported_at'])


def downgrade():
    op.drop_index('idx_hazards_reported_at', 'hazard_reports')
    op.drop_index('idx_hazards_status_expires', 'hazard_reports')
    op.drop_index('idx_riders_verified', 'riders')
    op.drop_index('idx_riders_location_status', 'riders')
    op.drop_index('idx_riders_status', 'riders')
    op.drop_index('idx_emergency_jobs_assigned_rider', 'emergency_jobs')
    op.drop_index('idx_emergency_jobs_village_status', 'emergency_jobs')
    op.drop_index('idx_emergency_jobs_status_created', 'emergency_jobs')
