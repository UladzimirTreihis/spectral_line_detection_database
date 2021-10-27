"""galaxy name in lines

Revision ID: 1aa9585a07c7
Revises: 473be8cdf721
Create Date: 2021-10-20 02:11:31.743155

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1aa9585a07c7'
down_revision = '473be8cdf721'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.add_column(sa.Column('galaxy_name', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('templine', schema=None) as batch_op:
        batch_op.drop_column('galaxy_name')

    # ### end Alembic commands ###
