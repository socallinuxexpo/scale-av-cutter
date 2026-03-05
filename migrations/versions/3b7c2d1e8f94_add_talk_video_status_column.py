"""Add talk video_status column

Revision ID: 3b7c2d1e8f94
Revises: e3a1f9c2b4d7
Create Date: 2026-03-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3b7c2d1e8f94'
down_revision = 'e3a1f9c2b4d7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('talk',
        sa.Column('video_status', sa.VARCHAR(), nullable=False, server_default='No video')
    )

def downgrade():
    op.drop_column('talk', 'video_status')
