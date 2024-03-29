"""rename public key field

Revision ID: 2b986597b84a
Revises: 1a0ab1892776
Create Date: 2022-10-07 00:26:16.553669

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2b986597b84a'
down_revision = '1a0ab1892776'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pass_key', sa.Column('public_key', sa.LargeBinary(), nullable=True))
    op.alter_column('pass_key', 'createdAt',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_column('pass_key', 'public_key_spi')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pass_key', sa.Column('public_key_spi', postgresql.BYTEA(), autoincrement=False, nullable=True))
    op.alter_column('pass_key', 'createdAt',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False,
               existing_server_default=sa.text('CURRENT_TIMESTAMP'))
    op.drop_column('pass_key', 'public_key')
    # ### end Alembic commands ###
