"""Add checked_out_by and last_edited_by

Revision ID: 2ffe8f727155
Revises: 0a4525bcdddc
Create Date: 2022-08-20 15:25:18.709651

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2ffe8f727155'
down_revision = '0a4525bcdddc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('room_day',
        sa.Column('checked_out_by', sa.TEXT(), nullable=False, server_default="")
    )
    op.add_column('talk',
        sa.Column('last_edited_by', sa.TEXT(), nullable=False, server_default="")
    )


def downgrade():
    op.drop_column('room_day', 'checked_out_by')
    op.drop_column('talk', 'last_edited_by')
