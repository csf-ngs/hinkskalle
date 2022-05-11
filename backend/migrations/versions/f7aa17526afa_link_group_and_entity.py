"""link group and entity

Revision ID: f7aa17526afa
Revises: 2b9677bd1a22
Create Date: 2022-04-26 00:20:45.312736

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7aa17526afa'
down_revision = '2b9677bd1a22'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('entity') as batch_op:
      batch_op.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
      batch_op.create_unique_constraint(op.f('uq_entity_group_id'), ['group_id'])
      batch_op.create_foreign_key(op.f('fk_entity_group_id_group'), 'group', ['group_id'], ['id'])
    with op.batch_alter_table('group') as batch_op:
      batch_op.create_foreign_key(op.f('fk_group_createdBy_user'), 'user', ['createdBy'], ['username'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_group_createdBy_user'), 'group', type_='foreignkey')
    op.drop_constraint(op.f('fk_entity_group_id_group'), 'entity', type_='foreignkey')
    op.drop_constraint(op.f('uq_entity_group_id'), 'entity', type_='unique')
    op.drop_column('entity', 'group_id')
    # ### end Alembic commands ###
