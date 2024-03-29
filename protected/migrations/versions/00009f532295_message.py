"""message

Revision ID: 00009f532295
Revises: 6b351638072c
Create Date: 2021-09-15 13:13:13.563223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00009f532295'
down_revision = '6b351638072c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('editgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_id', sa.Integer(), nullable=False))

    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.drop_column('is_edited')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_edited', sa.VARCHAR(length=128), nullable=True))

    with op.batch_alter_table('editgalaxy', schema=None) as batch_op:
        batch_op.drop_column('original_id')

    # ### end Alembic commands ###
