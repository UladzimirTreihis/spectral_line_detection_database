"""not null 2

Revision ID: ec6d4041dc3b
Revises: 7def96f706bd
Create Date: 2021-07-06 15:59:03.452551

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec6d4041dc3b'
down_revision = '7def96f706bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.alter_column('galaxy_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.alter_column('galaxy_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
