"""first

Revision ID: 65bd7517a82e
Revises: ce9641c4cfef
Create Date: 2021-08-29 19:51:00.711838

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65bd7517a82e'
down_revision = 'ce9641c4cfef'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('galaxy',
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tempgalaxy',
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
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('university', sa.String(length=120), nullable=True),
    sa.Column('website', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('about_me', sa.String(length=140), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('line',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('galaxy_id', sa.Integer(), nullable=True),
    sa.Column('j_upper', sa.Integer(), nullable=False),
    sa.Column('integrated_line_flux', sa.Float(precision=32), nullable=False),
    sa.Column('integrated_line_flux_uncertainty_positive', sa.Float(precision=32), nullable=False),
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
    sa.ForeignKeyConstraint(['galaxy_id'], ['galaxy.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('templine',
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
    sa.ForeignKeyConstraint(['galaxy_id'], ['tempgalaxy.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('templine')
    op.drop_table('line')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    op.drop_table('tempgalaxy')
    op.drop_table('galaxy')
    # ### end Alembic commands ###
