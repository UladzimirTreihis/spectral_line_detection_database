"""added admin notes to temp

Revision ID: ce9641c4cfef
Revises: b85ed6da4ada
Create Date: 2021-08-22 10:37:43.337077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce9641c4cfef'
down_revision = 'b85ed6da4ada'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_notes', sa.String(length=128), nullable=True))

    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.add_column(sa.Column('admin_notes', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.drop_column('admin_notes')

    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.drop_column('admin_notes')

    # ### end Alembic commands ###