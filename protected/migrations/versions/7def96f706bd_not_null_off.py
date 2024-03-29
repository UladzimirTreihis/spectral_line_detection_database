"""not null off

Revision ID: 7def96f706bd
Revises: 85c9b56c8f59
Create Date: 2021-07-06 15:57:02.898814

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7def96f706bd'
down_revision = '85c9b56c8f59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tempids', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

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

    with op.batch_alter_table('tempids', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'tempgalaxy', ['tempgalaxy_id'], ['id'])

    # ### end Alembic commands ###
