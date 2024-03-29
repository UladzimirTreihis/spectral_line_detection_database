"""message

Revision ID: 6b351638072c
Revises: 384b3695a6f2
Create Date: 2021-09-07 18:59:27.988985

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b351638072c'
down_revision = '384b3695a6f2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('editgalaxy',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('is_similar', sa.String(length=128), nullable=True),
    sa.Column('is_edited', sa.String(length=128), nullable=True),
    sa.Column('right_ascension', sa.Float(precision=32), nullable=False),
    sa.Column('declination', sa.Float(precision=32), nullable=False),
    sa.Column('coordinate_system', sa.String(length=128), nullable=False),
    sa.Column('redshift', sa.Float(precision=32), nullable=True),
    sa.Column('redshift_error', sa.Float(precision=32), nullable=True),
    sa.Column('lensing_flag', sa.String(length=32), nullable=False),
    sa.Column('classification', sa.String(length=128), nullable=False),
    sa.Column('notes', sa.String(length=128), nullable=True),
    sa.Column('user_submitted', sa.String(length=128), nullable=True),
    sa.Column('user_email', sa.String(length=128), nullable=True),
    sa.Column('admin_notes', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('editline',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('galaxy_id', sa.Integer(), nullable=True),
    sa.Column('from_existed_id', sa.Integer(), nullable=True),
    sa.Column('j_upper', sa.Integer(), nullable=False),
    sa.Column('integrated_line_flux', sa.Float(precision=32), nullable=False),
    sa.Column('integrated_line_flux_uncertainty_positive', sa.Float(precision=32), nullable=True),
    sa.Column('integrated_line_flux_uncertainty_negative', sa.Float(precision=32), nullable=True),
    sa.Column('peak_line_flux', sa.Float(precision=32), nullable=True),
    sa.Column('peak_line_flux_uncertainty_positive', sa.Float(precision=32), nullable=True),
    sa.Column('peak_line_flux_uncertainty_negative', sa.Float(precision=32), nullable=True),
    sa.Column('line_width', sa.Float(precision=32), nullable=True),
    sa.Column('line_width_uncertainty_positive', sa.Float(precision=32), nullable=True),
    sa.Column('line_width_uncertainty_negative', sa.Float(precision=32), nullable=True),
    sa.Column('observed_line_frequency', sa.Float(precision=32), nullable=True),
    sa.Column('observed_line_frequency_uncertainty_positive', sa.Float(precision=32), nullable=True),
    sa.Column('observed_line_frequency_uncertainty_negative', sa.Float(precision=32), nullable=True),
    sa.Column('detection_type', sa.String(length=32), nullable=True),
    sa.Column('observed_beam_major', sa.Float(precision=32), nullable=True),
    sa.Column('observed_beam_minor', sa.Float(precision=32), nullable=True),
    sa.Column('observed_beam_angle', sa.Float(precision=32), nullable=True),
    sa.Column('reference', sa.String(length=128), nullable=True),
    sa.Column('notes', sa.String(length=128), nullable=True),
    sa.Column('user_submitted', sa.String(length=128), nullable=True),
    sa.Column('user_email', sa.String(length=128), nullable=True),
    sa.Column('admin_notes', sa.String(length=128), nullable=True),
    sa.ForeignKeyConstraint(['galaxy_id'], ['editgalaxy.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('editline')
    op.drop_table('editgalaxy')
    # ### end Alembic commands ###
