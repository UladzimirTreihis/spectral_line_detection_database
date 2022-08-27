"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    ${upgrades if upgrades else "pass"}
    op.alter_column('line', 'observed_line_frequency', new_column_name='observed_line_redshift')
    op.alter_column('line', 'observed_line_frequency_uncertainty_positive', new_column_name='observed_line_redshift_uncertainty_positive')
    op.alter_column('line', 'observed_line_frequency_uncertainty_negative', new_column_name='observed_line_redshift_uncertainty_negative')
    op.alter_column('templine', 'observed_line_frequency', new_column_name='observed_line_redshift')
    op.alter_column('templine', 'observed_line_frequency_uncertainty_positive', new_column_name='observed_line_redshift_uncertainty_positive')
    op.alter_column('templine', 'observed_line_frequency_uncertainty_negative', new_column_name='observed_line_redshift_uncertainty_negative')
    op.alter_column('editline', 'observed_line_frequency', new_column_name='observed_line_redshift')
    op.alter_column('editline', 'observed_line_frequency_uncertainty_positive', new_column_name='observed_line_redshift_uncertainty_positive')
    op.alter_column('editline', 'observed_line_frequency_uncertainty_negative', new_column_name='observed_line_redshift_uncertainty_negative')


def downgrade():
    ${downgrades if downgrades else "pass"}
