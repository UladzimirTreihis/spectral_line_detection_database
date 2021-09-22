"""message

Revision ID: 1aad68735dd0
Revises: 00009f532295
Create Date: 2021-09-15 13:14:37.608672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1aad68735dd0'
down_revision = '00009f532295'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('editgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_id', sa.Integer(), nullable=True))

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
