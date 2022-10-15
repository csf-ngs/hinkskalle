"""merge quota and passkeys

Revision ID: 1a0ab1892776
Revises: 379ae3b3b0a1, e6a059697053
Create Date: 2022-09-30 22:22:24.566808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1a0ab1892776"
down_revision = ("379ae3b3b0a1", "e6a059697053")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
