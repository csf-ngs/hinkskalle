"""size column bigint

Revision ID: 176eef8ffb6a
Revises: 3e2d8b975154
Create Date: 2021-05-07 15:56:45.293212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '176eef8ffb6a'
down_revision = '3e2d8b975154'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(op.f('uq_image_upload_url_id'), 'image_upload_url', ['id'])
    op.alter_column(table_name='image', column_name='size', type_=sa.BigInteger)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_image_upload_url_id'), 'image_upload_url', type_='unique')
    # ### end Alembic commands ###
