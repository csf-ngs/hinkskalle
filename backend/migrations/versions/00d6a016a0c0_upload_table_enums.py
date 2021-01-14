"""upload table enums

Revision ID: 00d6a016a0c0
Revises: 4a9ed54c3e89
Create Date: 2021-01-08 14:52:23.273088

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00d6a016a0c0'
down_revision = '4a9ed54c3e89'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image_upload_url', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.Enum('single', 'multipart', name='uploadtypes'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image_upload_url', schema=None) as batch_op:
        batch_op.drop_column('type')

    # ### end Alembic commands ###