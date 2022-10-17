"""one-to-many manifest to tags

Revision ID: b12c651bc0db
Revises: ff9569b2a175
Create Date: 2021-06-04 13:04:21.604686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b12c651bc0db"
down_revision = "ff9569b2a175"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("manifest") as batch_op:
        batch_op.drop_constraint("uq_manifest_tag_id", type_="unique")
        batch_op.drop_constraint("fk_manifest_tag_id_tag", type_="foreignkey")
        batch_op.drop_column("tag_id")
    with op.batch_alter_table("tag") as batch_op:
        batch_op.add_column(sa.Column("manifest_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(op.f("fk_tag_manifest_id_manifest"), "manifest", ["manifest_id"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("fk_tag_manifest_id_manifest"), "tag", type_="foreignkey")
    op.drop_column("tag", "manifest_id")
    op.add_column("manifest", sa.Column("tag_id", sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key("fk_manifest_tag_id_tag", "manifest", "tag", ["tag_id"], ["id"])
    op.create_unique_constraint("uq_manifest_tag_id", "manifest", ["tag_id"])
    # ### end Alembic commands ###
