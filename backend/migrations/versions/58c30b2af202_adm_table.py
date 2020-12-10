"""adm table

Revision ID: 58c30b2af202
Revises: 5845d3b8cbdb
Create Date: 2020-12-10 16:21:48.272814

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58c30b2af202'
down_revision = '5845d3b8cbdb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('adm',
    sa.Column('key', sa.Enum('ldap_sync_results', name='admkeys'), nullable=False),
    sa.Column('val', sa.JSON(), nullable=False),
    sa.Column('createdAt', sa.DateTime(), nullable=True),
    sa.Column('createdBy', sa.String(), nullable=True),
    sa.Column('updatedAt', sa.DateTime(), nullable=True),
    sa.Column('updatedBy', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_adm'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('adm')
    # ### end Alembic commands ###
