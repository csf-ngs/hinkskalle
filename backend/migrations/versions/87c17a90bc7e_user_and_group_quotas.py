"""user and group quotas

Revision ID: 87c17a90bc7e
Revises: 4d5488f98f01
Create Date: 2022-09-18 01:16:43.657284

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '87c17a90bc7e'
down_revision = '4d5488f98f01'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('group', sa.Column('quota', sa.BigInteger(), nullable=True))
    op.add_column('user', sa.Column('quota', sa.BigInteger(), nullable=True))
    op.get_bind().execute("""
        UPDATE "user" SET quota=COALESCE((SELECT max(quota) FROM entity WHERE "createdBy"="user".username), 0)
    """)
    op.get_bind().execute("""
        UPDATE "group" SET quota=COALESCE((SELECT max(quota) FROM entity WHERE group_id="group".id), 0)
    """)

    op.drop_column('entity', 'quota')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entity', sa.Column('quota', sa.BIGINT(), autoincrement=False, nullable=True))
    op.get_bind().execute("""
        UPDATE entity SET quota=COALESCE(
            (SELECT quota FROM "group" WHERE "group".id=group_id),
            (SELECT quota FROM "user" WHERE entity."createdBy"="user".username),
            0
        )
    """)

    op.drop_column('user', 'quota')
    op.drop_column('group', 'quota')
    # ### end Alembic commands ###
