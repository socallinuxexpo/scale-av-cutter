"""Add talk notes column

Revision ID: b20c3b486b36
Revises: d7b68e59e864
Create Date: 2022-07-27 00:11:27.341811

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b20c3b486b36'
down_revision = 'd7b68e59e864'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('talk',
        sa.Column('notes', sa.TEXT(), nullable=False, server_default="")
    )

def downgrade():
    op.drop_column('talk', 'notes')
