from flask_wtf import FlaskForm
from wtforms import FileField, FloatField, StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import Regexp, ValidationError, DataRequired, Length, URL, Optional, NumberRange
from flask import request
from config import dec_reg_exp, ra_reg_exp, ref_reg_exp
from app.models import User
from species import species as species_choices

classification_choices = [('LBG', 'LBG (Lyman Break Galaxy)'),
                          ('MS', 'MS (Main Sequence Galaxy)'),
                          ('SMG', 'SMG (Submillimeter Galaxy)'),
                          ('DSFG', 'DSFG (Dusty Star-Forming Galaxy)'),
                          ('SB', 'SB (Starburst)'),
                          ('AGN', 'AGN (Active Galactic Nucleus)'),
                          ('QSO', 'QSO (Optically Bright AGN)'),
                          ('Quasar', 'Quasar (Optical and Radio Bright AGN)'),
                          ('RQ-AGN', 'RQ-AGN (Radio-Quiet AGN)'),
                          ('RL-AGN', 'RL-AGN (Radio-Loud AGN)'),
                          ('RG', 'RG (Radio Galaxy)'),
                          ('BzK', 'BzK (BzK-selected Galaxy)'),
                          ('ERO', 'ERO (Extremely Red Object)')]


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    university = StringField('University Affiliation', validators=[Optional()])
    website = StringField('Website', validators=[Optional(), URL()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    # Yet to understand the method
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    # If the username has changed to something but original_username, then query if new username is not in the database,
    # if it is, raise ValidationError
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')


# The simple search form to display options also. Will need to redevelop to be either advanced or just simple search.
class SearchForm(FlaskForm):
    search = StringField('')
    submit = SubmitField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)


class AdvancedSearchForm(FlaskForm):

    name = StringField('Galaxy Name', validators=[Optional()])
    right_ascension_min = StringField('Right Ascension min:', validators=[
        Regexp(ra_reg_exp, message="Input in the format 00h00m00s, 00h00\'00\", or as a float [-90, +90]"), Optional()])
    right_ascension_max = StringField('Right Ascension max:', validators=[
        Regexp(ra_reg_exp, message="Input in the format 00h00m00s, 00h00\'00\", or as a float [-90, +90]"), Optional()])
    declination_min = StringField('Declination min:', validators=[
        Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s, (+/-)00d00\'00\", or as a float [0, 360]"), Optional()])
    declination_max = StringField('Declination max:', validators=[
        Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s, (+/-)00d00\'00\", or as a float [0, 360]"), Optional()])

    right_ascension_point = StringField('Right Ascension', validators=[
        Regexp(ra_reg_exp, message="Input in the format 00h00m00s, 00h00\'00\", or as a float [-90, +90]"), Optional()])
    declination_point = StringField('Declination', validators=[
        Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s, (+/-)00d00\'00\", or as a float [0, 360]"), Optional()])

    radius_d = FloatField('deg', validators=[Optional(), NumberRange(min=0, max=180)])
    radius_m = FloatField('arcmin', validators=[Optional(), NumberRange(min=0, max=60)])
    radius_s = FloatField('arcsec', validators=[Optional(), NumberRange(min=0, max=60)])

    redshift_min = FloatField('Redshift min:', validators=[Optional()])
    redshift_max = FloatField('Redshift max:', validators=[Optional()])
    lensing_flag = SelectField(u'Gravitational Lensing',
                               choices=[('Either', 'Either'), ('Lensed', 'Lensed'), ('Unlensed', 'Unlensed')],
                               validate_choice=False)
    classification = SelectMultipleField(u'Include Classification',
                                         choices=classification_choices,
                                         validate_choice=False,
                                         render_kw = {"multiselect-search":"true", "multiselect-select-all":"true"})
    remove_classification = SelectMultipleField(u'Exclude Classification',
                                        choices=classification_choices,
                                        validate_choice=False,
                                        render_kw = {"multiselect-search":"true", "multiselect-select-all":"true"})

    # Line data

    emitted_frequency_min = FloatField('Emitted Frequency (GHz) min:', validators=[Optional(), NumberRange(min=0)])
    emitted_frequency_max = FloatField('Emitted Frequency (GHz) max:', validators=[Optional(), NumberRange(min=0)])
    species = SelectMultipleField(u'Select Species', choices=species_choices,
                          validate_choice=False,
                          render_kw = {"multiselect-search":"true", "multiselect-select-all":"true"})
    remove_species = SelectMultipleField(u'Exclude Species',
                                        choices=species_choices,
                                        validate_choice=False,
                                        render_kw = {"multiselect-search":"true", "multiselect-select-all":"true"})
    integrated_line_flux_min = FloatField('Integrated Line Flux (Jy*km/s) min:',
                                          validators=[Optional(), NumberRange(min=0)])
    integrated_line_flux_max = FloatField('Integrated Line Flux (Jy*km/s) max:',
                                          validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_min = FloatField('Peak Line Flux (mJy) min:', validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_max = FloatField('Peak Line Flux (mJy) max:', validators=[Optional(), NumberRange(min=0)])
    line_width_min = FloatField('Line FWHM (km/s) min:', validators=[Optional(), NumberRange(min=0)])
    line_width_max = FloatField('Line FWHM (km/s) max:', validators=[Optional(), NumberRange(min=0)])

    observed_line_redshift_min = FloatField('Observed Line Redshift min:',
                                             validators=[Optional(), NumberRange(min=0)])
    observed_line_redshift_max = FloatField('Observed Line Redshift max:',
                                             validators=[Optional(), NumberRange(min=0)])

    detection_type = SelectField(u'Telescope Type',
                                 choices=[('Either', 'Either'), ('Single Dish', 'Single Dish'),
                                          ('Interferometric', 'Interferometric')], validate_choice=False)
    observed_beam_major_min = FloatField('Beam Major Axis FWHM (arcsec) min:',
                                         validators=[Optional(), NumberRange(min=0)])
    observed_beam_major_max = FloatField('Beam Major Axis FWHM (arcsec) max:',
                                         validators=[Optional(), NumberRange(min=0)])
    observed_beam_minor_min = FloatField('Beam Minor Axis FWHM (arcsec) min:',
                                         validators=[Optional(), NumberRange(min=0)])
    observed_beam_minor_max = FloatField('Beam Minor Axis FWHM (arcsec) max:',
                                         validators=[Optional(), NumberRange(min=0)])

    reference = StringField('Citation (use ADS bibcode, example:  2019ApJ...879...52S)', validators=[Regexp(ref_reg_exp, message="Check Bibcode format"), Optional()])

    galaxySearch = SubmitField(label='Search')
    # lineSearch = SubmitField(label="Search for Lines")


class AddGalaxyForm(FlaskForm):
    name = StringField('Galaxy Name', validators=[DataRequired()])
    right_ascension = StringField('Right Ascension',
                                  validators=[Regexp(ra_reg_exp, message="Input in the format 00h00m00s, 00h00\'00\", or as a float [-90, +90]"),
                                              DataRequired()])
    declination = StringField('Declination', validators=[
        Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s, (+/-)00d00\'00\", or as a float [0, 360]"), DataRequired()])
    submit_anyway = SubmitField('Submit Anyway')
    do_not_submit = SubmitField('No, go back to Home. ')
    coordinate_system = SelectField(u'Coordinate System', choices=[('J2000', 'J2000'), ('ICRS', 'ICRS')],
                                    validators=[DataRequired()])
    lensing_flag = SelectField(u'Is it gravitationally lensed?',
                               choices=[('Lensed', 'Lensed'), ('Unlensed', 'Unlensed'), ('Unknown', 'Unknown')],
                               validators=[DataRequired()])
    classification = SelectMultipleField(u'Classification (Press ctrl/cmd to select all that apply)',
                                         choices=classification_choices)
    notes = StringField('Notes', validators=[Optional()])
    submit = SubmitField('Submit')
    new_line = SubmitField('Add A New Line to this Galaxy')


class EditGalaxyForm(FlaskForm):
    name = StringField('Galaxy Name', validators=[DataRequired()])
    submit_anyway = SubmitField('Submit Anyway')
    do_not_submit = SubmitField('No, go back to Home. ')
    coordinate_system = SelectField(u'Coordinate System', choices=[('J2000', 'J2000'), ('ICRS', 'ICRS')],
                                    validators=[DataRequired()])
    lensing_flag = SelectField(u'Is it gravitationally lensed?',
                               choices=[('Lensed', 'Lensed'), ('Unlensed', 'Unlensed'), ('Unknown', 'Unknown')],
                               validators=[DataRequired()])
    classification = StringField('Current Classification', validators=[DataRequired()])
    remove_classification = SelectMultipleField(u'Remove Classification (Press ctrl/cmd to select all that apply)',
                                                choices=classification_choices)
    add_classification = SelectMultipleField(u'Add Classification (Press ctrl/cmd to select all that apply)',
                                             choices=classification_choices)
    notes = StringField('Notes', validators=[Optional()])
    submit = SubmitField('Submit')
    new_line = SubmitField('Add Line to this Galaxy')


class DynamicSearchForm(FlaskForm):
    galaxy_name = StringField('Galaxy', validators=[DataRequired(), Length(max=40)],
                              render_kw={"placeholder": "Galaxy Name"})
    submit = SubmitField('View Galaxy')


class AddLineForm(FlaskForm):
    galaxy_name = StringField('Galaxy Name', validators=[DataRequired(), Length(max=40)],
                              render_kw={"placeholder": "Search Galaxy Name"})
    galaxy_form = SubmitField('Add a New Galaxy ')
    emitted_frequency = StringField('Emitted Frequency', validators=[DataRequired()])
    species = SelectField(u'Select Species', choices=species_choices, validators=[DataRequired()])
    right_ascension = StringField('Right Ascension', validators=[DataRequired()])
    declination = StringField('Declination', validators=[DataRequired()])
    integrated_line_flux = FloatField('Integrated Line Flux (in Jy*km/s)',
                                      validators=[DataRequired(), NumberRange(min=0)])
    integrated_line_flux_uncertainty_positive = FloatField('Integrated Line Flux Uncertainty (in Jy*km/s)',
                                                           validators=[DataRequired(), NumberRange(min=0)])
    integrated_line_flux_uncertainty_negative = FloatField('Integrated Line Flux Negative Uncertainty',
                                                           validators=[Optional(), NumberRange(min=0)])
    peak_line_flux = FloatField('Peak Line Flux (in mJy)', validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_uncertainty_positive = FloatField('Peak Line Flux Uncertainty (in mJy)',
                                                     validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_uncertainty_negative = FloatField('Peak Line Flux Negative Uncertainty',
                                                     validators=[Optional(), NumberRange(min=0)])
    line_width = FloatField('Line Full Width Half Max (in km/s)', validators=[Optional(), NumberRange(min=0)])
    line_width_uncertainty_positive = FloatField('Line FWHM Uncertainty (in km/s)',
                                                 validators=[Optional(), NumberRange(min=0)])
    line_width_uncertainty_negative = FloatField('Line FWHM Negative Uncertainty',
                                                 validators=[Optional(), NumberRange(min=0)])
    freq_type = SelectField(u'Enter line center as redshift (z) or observed frequency (f in units of GHz)',
                            choices=[('z', 'z'), ('f', 'f')],
                            validators=[DataRequired()])
    observed_line_redshift = FloatField('Observed Frequency/Redshift', validators=[Optional(), NumberRange(min=0)])
    observed_line_redshift_uncertainty_positive = FloatField('Observed Frequency/Redshift Uncertainty (same units)',
                                                              validators=[Optional(), NumberRange(min=0)])
    observed_line_redshift_uncertainty_negative = FloatField('Observed Frequency/Redshift Negative Uncertainty',
                                                              validators=[Optional(), NumberRange(min=0)])
    detection_type = SelectField(u'Telescope Type used for Observation',
                                 choices=[('SD', 'Single Dish'), ('IF', 'Interferometric')],
                                 validators=[Optional()])
    observed_beam_major = FloatField('Beam Major Axrs FWHM (in arcsec) (strongly recommended) ',
                                     validators=[Optional(), NumberRange(min=0)])
    observed_beam_minor = FloatField('Observed Beam Minor Axrs FWHM (in arcsec) (strongly recommended) ',
                                     validators=[Optional(), NumberRange(min=0)])
    observed_beam_angle = FloatField('Beam Position Angle (in degrees) (strongly recommended)',
                                     validators=[Optional()])
    reference = StringField('Citation (use ADS bibcode, example:  2019ApJ...879...52S)', validators=[Regexp(ref_reg_exp, message="Check Bibcode format"), Optional()])
    notes = StringField('Notes', validators=[Optional()])
    submit = SubmitField('Submit')


class EditLineForm(FlaskForm):
    galaxy_name = StringField('Galaxy Name', validators=[DataRequired(), Length(max=40)],
                              render_kw={"placeholder": "Search Galaxy Name"})
    galaxy_form = SubmitField('Add a New Galaxy ')
    emitted_frequency = FloatField('Emitted Frequency', validators=[DataRequired(), NumberRange(min=0)])
    species = SelectField(u'Select Species', choices=species_choices, validators=[DataRequired()])
    integrated_line_flux = FloatField('Integrated Line Flux', validators=[DataRequired(), NumberRange(min=0)])
    integrated_line_flux_uncertainty_positive = FloatField('Integrated Line Flux Positive Uncertainty',
                                                           validators=[DataRequired(), NumberRange(min=0)])
    integrated_line_flux_uncertainty_negative = FloatField('Integrated Line Flux Negative Uncertainty',
                                                           validators=[Optional(), NumberRange(min=0)])
    peak_line_flux = FloatField('Peak Line Flux', validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_uncertainty_positive = FloatField('Peak Line Flux Positive Uncertainty',
                                                     validators=[Optional(), NumberRange(min=0)])
    peak_line_flux_uncertainty_negative = FloatField('Peak Line Flux Negative Uncertainty',
                                                     validators=[Optional(), NumberRange(min=0)])
    line_width = FloatField('Line Width', validators=[Optional(), NumberRange(min=0)])
    line_width_uncertainty_positive = FloatField('Line Width Positive Uncertainty',
                                                 validators=[Optional(), NumberRange(min=0)])
    line_width_uncertainty_negative = FloatField('Line Width Negative Uncertainty',
                                                 validators=[Optional(), NumberRange(min=0)])
    freq_type = SelectField(u'Enter as redshift (z) or observed frequency (f)', choices=[('z', 'z'), ('f', 'f')],
                            validators=[DataRequired()])
    observed_line_redshift = FloatField('Observable Line Frequency', validators=[Optional(), NumberRange(min=0)])
    observed_line_redshift_uncertainty_positive = FloatField('Observable Line Frequency Positive Uncertainty',
                                                              validators=[Optional(), NumberRange(min=0)])
    observed_line_redshift_uncertainty_negative = FloatField('Observable Line Frequency Negative Uncertainty',
                                                              validators=[Optional(), NumberRange(min=0)])
    detection_type = SelectField(u'Telescope Type used for Detection',
                                 choices=[('SD', 'Single Dish'), ('IF', 'Interferometric')],
                                 validators=[Optional()])
    observed_beam_major = FloatField('Observed Beam Major (FwHM in arcsec) (strongly recommended) ',
                                     validators=[Optional(), NumberRange(min=0)])
    observed_beam_minor = FloatField('Observed Beam Minor (FwHM in arcsec) (strongly recommended) ',
                                     validators=[Optional(), NumberRange(min=0)])
    observed_beam_angle = FloatField('Observed Beam Position Angle in Degrees (strongly recommended) ',
                                     validators=[Optional()])
    reference = StringField('Citation (use ADS bibcode, example:  2019ApJ...879...52S)', validators=[Regexp(ref_reg_exp, message="Check Bibcode format"), Optional()])
    notes = StringField('Notes', validators=[Optional()])
    submit = SubmitField('Submit')


class UploadFileForm(FlaskForm):
    file = FileField('Choose File For Upload')
    submit = SubmitField('Submit')
