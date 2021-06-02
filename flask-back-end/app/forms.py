from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.core import SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, URL, Optional, NumberRange
from app.models import User, Galaxy, Line
from flask import request

#creating a log-in form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Official Email', validators=[DataRequired(), Email()])
    university = StringField('University Affiliation', validators=[Optional()])
    website = StringField('Website', validators=[Optional(), URL ()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
            
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
    #if the username has changed to something but original_uername, then query if new username is not in the database, if it is, raise ValidationError
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

class ButtonForm(FlaskForm):
    submit = SubmitField('Advanced Search', validators=[DataRequired()])

class AdvancedSearchForm(FlaskForm):
    name = StringField('Galaxy Name', validators = [Optional ()])
    right_ascension_min = FloatField('Right Ascension from:', validators = [Optional ()])
    right_ascension_max = FloatField('Right Ascension to:', validators = [Optional ()])
    declination_min = FloatField('Declination from:', validators = [Optional ()])
    declination_max = FloatField('Declination to:', validators = [Optional ()])
    redshift_min = FloatField('Redshift from:', validators = [Optional ()])
    redshift_max = FloatField('Redshift to:', validators = [Optional ()])
    lensing_flag = SelectField(u'Lensing Flag',
        choices = [('Lensed', 'Lensed'), ('Unlensed', 'Unlensed ')], validate_choice=False)
    submit = SubmitField('Submit')
    
class AddGalaxyForm(FlaskForm):
    name = StringField('Galaxy Name', validators = [DataRequired ()])
    right_ascension = FloatField('Right Ascension', validators = [DataRequired (), NumberRange(min = 0)])
    declination = FloatField('Declination', validators = [DataRequired ()])
    coordinate_system = StringField('Coordinate System', validators = [DataRequired ()])
    redshift = FloatField('Redshift', validators = [Optional (), NumberRange(min = 0)])
    lensing_flag = StringField('Lensing Flag', validators = [DataRequired ()])
    classification = StringField('Classification', validators = [DataRequired ()])
    notes = StringField('Notes', validators = [Optional ()])
    submit = SubmitField('Submit')
    new_line = SubmitField ('Add Line to this Galaxy')

class AddLineForm(FlaskForm):
    galaxy_name = SelectField (u'Galaxy Name', choices = Galaxy.query.with_entities(Galaxy.name).all())
    galaxy_id = IntegerField('Galaxy ID (from database) ')
    j_upper = IntegerField('J Upper', validators = [DataRequired (), NumberRange(min = 0)])
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