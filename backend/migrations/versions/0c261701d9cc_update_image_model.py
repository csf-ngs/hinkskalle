"""update image model

Revision ID: 0c261701d9cc
Revises: 58c30b2af202
Create Date: 2021-01-04 21:22:21.597208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c261701d9cc'
down_revision = '58c30b2af202'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image', schema=None) as batch_op:
        batch_op.add_column(sa.Column('arch', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('encrypted', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('signed', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('image', schema=None) as batch_op:
        batch_op.drop_column('signed')
        batch_op.drop_column('encrypted')
        batch_op.drop_column('arch')

    # ### end Alembic commands ###
