"""merged 2

Revision ID: ea200bef055e
Revises: 1d84406ba92d
Create Date: 2021-09-22 13:31:26.924132

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea200bef055e'
down_revision = '1d84406ba92d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.drop_column('is_edited')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_edited', sa.VARCHAR(length=128), nullable=True))

    # ### end Alembic commands ###
