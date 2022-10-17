"""add source, token, unique constraints

Revision ID: c4577b8a9c60
Revises: 0569209455b1
Create Date: 2020-11-06 15:32:51.469605

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c4577b8a9c60"
down_revision = "0569209455b1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source", sa.String(), nullable=False, server_default="local"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("source")

    with op.batch_alter_table("token", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_token_token"), type_="unique")

    with op.batch_alter_table("entity", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_entity_name"), type_="unique")

    # ### end Alembic commands ###
