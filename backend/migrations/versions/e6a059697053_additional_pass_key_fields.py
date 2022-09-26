"""additional pass key fields

Revision ID: e6a059697053
Revises: 99cb63a11ecc
Create Date: 2022-09-26 20:36:23.939438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6a059697053'
down_revision = '99cb63a11ecc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pass_key', sa.Column('createdAt', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()))
    op.add_column('pass_key', sa.Column('last_used', sa.DateTime(), nullable=True))
    op.add_column('pass_key', sa.Column('login_count', sa.Integer(), nullable=True, server_default="0"))
    op.create_unique_constraint('pass_key_name_user_id_idx', 'pass_key', ['user_id', 'name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pass_key_name_user_id_idx', 'pass_key', type_='unique')
    op.drop_column('pass_key', 'login_count')
    op.drop_column('pass_key', 'last_used')
    op.drop_column('pass_key', 'createdAt')
    # ### end Alembic commands ###