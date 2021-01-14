"""more signature fields

Revision ID: b15a9e0cdc6e
Revises: 95690d82cbf2
Create Date: 2021-01-05 13:57:12.681106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b15a9e0cdc6e'
down_revision = '95690d82cbf2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sigdata', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image', schema=None) as batch_op:
        batch_op.drop_column('sigdata')

    # ### end Alembic commands ###