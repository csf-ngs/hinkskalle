"""downloadCount field on manifests

Revision ID: b63bba1322d5
Revises: 2800a86f2d6f
Create Date: 2021-06-21 15:16:52.707599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b63bba1322d5'
down_revision = '2800a86f2d6f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('manifest', sa.Column('downloadCount', sa.Integer(), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text('UPDATE manifest SET "downloadCount"=0'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('manifest', 'downloadCount')
    # ### end Alembic commands ###
