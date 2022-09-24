"""passkeys

Revision ID: 99cb63a11ecc
Revises: 4d5488f98f01
Create Date: 2022-09-24 00:47:55.978382

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99cb63a11ecc'
down_revision = '4d5488f98f01'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pass_key',
    sa.Column('id', sa.LargeBinary(length=16), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('public_key_spi', sa.LargeBinary(), nullable=True),
    sa.Column('backed_up', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_pass_key_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_pass_key'))
    )
    op.add_column('user', sa.Column('passkey_id', sa.LargeBinary(length=16), nullable=True))
    op.create_unique_constraint(op.f('uq_user_passkey_id'), 'user', ['passkey_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('uq_user_passkey_id'), 'user', type_='unique')
    op.drop_column('user', 'passkey_id')
    op.drop_table('pass_key')
    # ### end Alembic commands ###
