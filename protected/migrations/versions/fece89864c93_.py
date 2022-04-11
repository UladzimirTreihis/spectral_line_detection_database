"""empty message

Revision ID: fece89864c93
Revises: 
Create Date: 2021-05-13 16:55:14.474960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fece89864c93'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('galaxy',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('right_ascension', sa.Float(precision=32), nullable=True),
    sa.Column('declination', sa.Float(precision=32), nullable=True),
    sa.Column('coordinate_system', sa.String(length=128), nullable=True),
    sa.Column('redshift', sa.Float(precision=32), nullable=True),
    sa.Column('lensing_flag', sa.String(length=32), nullable=True),
    sa.Column('classification', sa.String(length=128), nullable=True),
    sa.Column('notes', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('line',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('galaxy_id', sa.Integer(), nullable=True),
    sa.Column('j_upper', sa.Integer(), nullable=True),
    sa.Column('line_id_type', sa.String(length=32), nullable=True),
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
    sa.ForeignKeyConstraint(['galaxy_id'], ['galaxy.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('line')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('galaxy')
    # ### end Alembic commands ###
