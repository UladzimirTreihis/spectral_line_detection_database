from flask_wtf import FlaskForm
from wtforms import FileField, IntegerField, FloatField, StringField, SubmitField, TextAreaField
from wtforms.fields.core import SelectField
from wtforms.validators import Regexp, ValidationError, DataRequired, Email, EqualTo, Length, URL, Optional, NumberRange
from flask import request
from config import dec_reg_exp, ra_reg_exp
from app.models import User


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    university = StringField('University Affiliation', validators=[Optional()])
    website = StringField('Website', validators=[Optional(), URL ()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    #Yet to understand the method
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    #if the username has changed to something but original_us  ername, then query if new username is not in the database, if it is, raise ValidationError
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')

#The simple search form to desplay options also. Will need to redevelop to be either advanced or just simple search.
class SearchForm(FlaskForm):
    search = StringField('')
    submit = SubmitField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

#Will delete if won't need anymore
#class ButtonForm(FlaskForm):
    #submit = SubmitField('Advanced Search', validators=[DataRequired()])


class AdvancedSearchForm(FlaskForm):
    name = StringField('Galaxy Name', validators = [Optional ()])
    right_ascension_min = StringField('Right Ascension from:', validators = [Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float"), Optional ()])
    right_ascension_max = StringField('Right Ascension to:', validators = [Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float"), Optional ()])
    declination_min = StringField('Declination from:', validators = [Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s or as a float"), Optional ()])
    declination_max = StringField('Declination to:', validators = [Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s or as a float"), Optional ()])

    right_ascension_point = StringField('Right Ascension', validators = [Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float"), Optional ()])
    declination_point = StringField('Declination', validators = [Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s or as a float"), Optional ()])

    radius_d = FloatField('deg', validators = [Optional (), NumberRange(min = 0, max = 180)])
    radius_m = FloatField('arcmin', validators = [Optional (), NumberRange(min = 0, max = 60)])
    radius_s = FloatField('arcsec', validators = [Optional (), NumberRange(min = 0, max = 60)])

    redshift_min = FloatField('Redshift from:', validators = [Optional ()])
    redshift_max = FloatField('Redshift to:', validators = [Optional ()])
    lensing_flag = SelectField(u'Lensing Flag',
        choices = [('Lensed', 'Lensed'), ('Unlensed', 'Unlensed'), ('Either', 'Either')], validate_choice=False)
    #line data

    j_upper_min = IntegerField('J Upper from:', validators = [Optional (), NumberRange(min = 0)])
    j_upper_max = IntegerField('J Upper to:', validators = [Optional (), NumberRange(min = 0)])
    line_id_type = StringField('Line ID Type', validators = [Optional ()])
    integrated_line_flux_min = FloatField('Integrated Line Flux from:', validators = [Optional(), NumberRange(min = 0)])
    integrated_line_flux_max = FloatField('Integrated Line Flux to:', validators = [Optional(), NumberRange(min = 0)])
    peak_line_flux_min = FloatField('Peak Line Flux from:', validators = [Optional (), NumberRange(min = 0)])
    peak_line_flux_max = FloatField('Peak Line Flux to:', validators = [Optional (), NumberRange(min = 0)])
    line_width_min = FloatField('Line Width from:', validators = [Optional (), NumberRange(min = 0)])
    line_width_max = FloatField('Line Width to:', validators = [Optional (), NumberRange(min = 0)])

    observed_line_frequency_min = FloatField('Observable Line Frequency from:', validators = [Optional (), NumberRange(min = 0)])
    observed_line_frequency_max = FloatField('Observable Line Frequency to:', validators = [Optional (), NumberRange(min = 0)])

    detection_type = SelectField(u'Detection Type',
        choices = [('Single Dish', 'Single Dish'), ('Interferometric', 'Interferometric'), ('Either', 'Either')], validate_choice=False)
    observed_beam_major_min = FloatField('Observed Beam Major from:', validators = [Optional (), NumberRange(min = 0)])
    observed_beam_major_max = FloatField('Observed Beam Major to:', validators = [Optional (), NumberRange(min = 0)])
    observed_beam_minor_min = FloatField('Observed Beam Minor from:', validators = [Optional (), NumberRange(min = 0)])
    observed_beam_minor_max = FloatField('Observed Beam Minor to:', validators = [Optional (), NumberRange(min = 0)])

    reference = StringField('Reference', validators = [Optional()])

    galaxySearch = SubmitField(label='Search for Galaxies')
    lineSearch = SubmitField(label="Search for Lines")

class AddGalaxyForm(FlaskForm):
    name = StringField('Galaxy Name', validators = [DataRequired ()])
    right_ascension = StringField('Right Ascension', validators = [Regexp(ra_reg_exp, message="Input in the format 00h00m00s or as a float"), DataRequired ()])
    declination = StringField('Declination', validators = [Regexp(dec_reg_exp, message="Input in the format (+/-)00d00m00s or as a float"), DataRequired ()])
    coordinate_system = SelectField(u'Coordinate System', choices = [('J2000', 'J2000'), ('ICRS', 'ICRS'), ('Enter as a float', 'Enter as a float')], validators = [DataRequired ()])
    redshift = FloatField('Redshift', validators = [Optional (), NumberRange(min = 0)])
    lensing_flag = SelectField(u'Lensing Flag', choices = [('Lensed', 'Lensed'), ('Unlensed', 'Unlensed'), ('Either', 'Either')], validators = [DataRequired ()])
    classification = StringField('Classification', validators = [DataRequired ()])
    notes = StringField('Notes', validators = [Optional ()])
    submit = SubmitField('Submit')
    new_line = SubmitField ('Add Line to this Galaxy')

class DynamicSearchForm(FlaskForm): 
    galaxy_name = StringField('Galaxy', validators=[DataRequired(),Length(max=40)],render_kw={"placeholder": "Galaxy Name"})

class AddLineForm(FlaskForm):
    galaxy_name = StringField('Galaxy Name', validators=[DataRequired(),Length(max=40)],render_kw={"placeholder": "Search Galaxy Name"})
    galaxy_form = SubmitField('Add a New Galaxy ')
    j_upper = IntegerField('J Upper', validators = [DataRequired (), NumberRange(min = 1, max=30, message="The database accepts J Upper between %(min)s and %(max)s")])
    line_id_type = StringField('Line ID Type', validators = [Optional ()])
    integrated_line_flux = FloatField('Integrated Line Flux', validators = [DataRequired(), NumberRange(min = 0)])
    integrated_line_flux_uncertainty_positive = FloatField('Positive Uncertainty', validators = [DataRequired (), NumberRange(min = 0)])
    integrated_line_flux_uncertainty_negative = FloatField('Negative Uncertainty', validators = [DataRequired (), NumberRange(max = 0)])
    peak_line_flux = FloatField('Peak Line Flux', validators = [Optional (), NumberRange(min = 0)])
    peak_line_flux_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional (), NumberRange(min = 0)])
    peak_line_flux_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional (), NumberRange(max = 0)])
    line_width = FloatField('Line Width', validators = [Optional (), NumberRange(min = 0)])
    line_width_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional (), NumberRange(min = 0)])
    line_width_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional (), NumberRange(max = 0)])
    observed_line_frequency = FloatField('Observable Line Frequency', validators = [Optional (), NumberRange(min = 0)])
    observed_line_frequency_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional (), NumberRange(min = 0)])
    observed_line_frequency_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional (), NumberRange(max = 0)])
    detection_type = StringField('Detection Type (strongly recommend) ', validators = [Optional ()])
    observed_beam_major = FloatField('Observed Beam Major (strongly recommend) ', validators = [Optional (), NumberRange(min = 0)])
    observed_beam_minor = FloatField('Observed Beam Minor (strongly recommend) ', validators = [Optional (), NumberRange(min = 0)])
    observed_beam_angle = FloatField('Observed Beam Angle (strongly recommend) ', validators = [Optional ()])
    reference = StringField('Reference', validators = [DataRequired()])
    notes = StringField('Notes', validators = [Optional ()])
    submit = SubmitField('Submit')

class UploadFileForm(FlaskForm):
    file = FileField('')
    submit = SubmitField('Submit')