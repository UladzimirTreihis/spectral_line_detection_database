"""is_similar

Revision ID: 3fa30d5deed9
Revises: f0b4a309c7aa
Create Date: 2021-07-05 17:53:07.708574

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fa30d5deed9'
down_revision = 'f0b4a309c7aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('galaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_similar', sa.String(length=128), nullable=True))

    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_similar', sa.String(length=128), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempgalaxy', schema=None) as batch_op:
        batch_op.drop_column('is_similar')

    with op.batch_alter_table('galaxy', schema=None) as batch_op:
        batch_op.drop_column('is_similar')

    # ### end Alembic commands ###
