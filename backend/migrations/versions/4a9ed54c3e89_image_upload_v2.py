"""image upload v2

Revision ID: 4a9ed54c3e89
Revises: b15a9e0cdc6e
Create Date: 2021-01-08 11:32:32.235084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a9ed54c3e89'
down_revision = 'b15a9e0cdc6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('image_upload_url',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('expiresAt', sa.DateTime(), nullable=True),
    sa.Column('path', sa.String(), nullable=False),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('md5sum', sa.String(), nullable=True),
    sa.Column('sha256sum', sa.String(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('createdAt', sa.DateTime(), nullable=True),
    sa.Column('createdBy', sa.String(), nullable=True),
    sa.Column('image_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['createdBy'], ['user.username'], name=op.f('fk_image_upload_url_createdBy_user')),
    sa.ForeignKeyConstraint(['image_id'], ['image.id'], name=op.f('fk_image_upload_url_image_id_image')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_image_upload_url')),
    sa.UniqueConstraint('id', name=op.f('uq_image_upload_url_id'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('image_upload_url')
    # ### end Alembic commands ###
