"""Change review status flow

Revision ID: adc38d830a08
Revises: 2ffe8f727155
Create Date: 2022-09-05 09:59:48.123717

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'adc38d830a08'
down_revision = '2ffe8f727155'
branch_labels = None
depends_on = None

review_status = sa.Enum("reviewing", "approved", "rejected", name="ReviewStatus")
edit_status = sa.Enum("incomplete", "done", "unusable", name="EditStatus")
tbl = sa.sql.table("talk",
    sa.Column("edit_status", edit_status, nullable=False),
    sa.Column("review_status", review_status, nullable=False)
)

def upgrade():
    op.execute(f"ALTER TABLE talk ALTER COLUMN review_status TYPE VARCHAR")
    op.execute(f"ALTER TABLE talk ALTER COLUMN edit_status TYPE VARCHAR")
    op.execute(tbl.update().where(tbl.c.review_status == "approved").where(tbl.c.edit_status == "unusable").values(review_status="unusable"))
    op.execute(tbl.update().where(tbl.c.review_status == "approved").where(tbl.c.edit_status == "done").values(review_status="done"))
    op.execute(tbl.update().where(tbl.c.review_status == "rejected").values(review_status="reviewing"))


def downgrade():
    op.execute(tbl.update().where(tbl.c.review_status == "unusable").where(tbl.c.edit_status == "unusable").values(review_status="approved"))
    op.execute(tbl.update().where(tbl.c.review_status == "done").where(tbl.c.edit_status == "done").values(review_status="approved"))
