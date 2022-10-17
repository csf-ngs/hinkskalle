"""disable password auth

Revision ID: 405171f14e02
Revises: 5fcba8a29da4
Create Date: 2022-10-09 21:19:21.035423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "405171f14e02"
down_revision = "5fcba8a29da4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("password_disabled", sa.Boolean(), server_default="false", nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "password_disabled")
    # ### end Alembic commands ###
