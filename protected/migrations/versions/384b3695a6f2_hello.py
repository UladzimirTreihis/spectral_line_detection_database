"""hello

Revision ID: 384b3695a6f2
Revises: ce9641c4cfef
Create Date: 2021-08-25 13:41:44.408281

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '384b3695a6f2'
down_revision = 'ce9641c4cfef'
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
