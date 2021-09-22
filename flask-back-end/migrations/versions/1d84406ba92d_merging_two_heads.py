"""merging two heads

Revision ID: 1d84406ba92d
Revises: 1aad68735dd0, b36bb1d6c155
Create Date: 2021-09-22 13:31:10.290693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d84406ba92d'
down_revision = ('1aad68735dd0', 'b36bb1d6c155')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
