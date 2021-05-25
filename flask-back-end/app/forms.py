from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, URL, Optional
from app.models import User

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

class AddGalaxyForm(FlaskForm):
    name = StringField('Galaxy Name', validators = [Optional ()])
    right_ascension = FloatField('Right Ascension', validators = [Optional ()])
    declination = FloatField('Declination', validators = [Optional ()])
    coordinate_system = StringField('Coordinate System', validators = [Optional ()])
    redshift = FloatField('Redshift', validators = [Optional ()])
    lensing_flag = StringField('Lensing Flag', validators = [Optional ()])
    classification = StringField('Classification', validators = [Optional ()])
    notes = StringField('Notes', validators = [Optional ()])
    submit = SubmitField('Submit')

class AddLineForm(FlaskForm):
    galaxy_id = IntegerField('Galaxy ID (from database) ')
    j_upper = IntegerField('J Upper', validators = [Optional ()])
    line_id_type = StringField('Line ID Type', validators = [Optional ()])
    integrated_line_flux = FloatField('Integrated Line Flux', validators = [DataRequired()])
    integrated_line_flux_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional ()])
    integrated_line_flux_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional ()])
    peak_line_flux = FloatField('Peak Line Flux', validators = [Optional ()])
    peak_line_flux_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional ()])
    peak_line_flux_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional ()])
    line_width = FloatField('Line Width', validators = [Optional ()])
    line_width_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional ()])
    line_width_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional ()])
    observed_line_frequency = FloatField('Observable Line Frequency', validators = [Optional ()])
    observed_line_frequency_uncertainty_positive = FloatField('Positive Uncertainty', validators = [Optional ()])
    observed_line_frequency_uncertainty_negative = FloatField('Negative Uncertainty', validators = [Optional ()])
    detection_type = StringField('Detection Type (strongly recommend) ', validators = [Optional ()])
    observed_beam_major = FloatField('Observed Beam Major (strongly recommend) ', validators = [Optional ()])
    observed_beam_minor = FloatField('Observed Beam Minor (strongly recommend) ', validators = [Optional ()])
    observed_beam_angle = FloatField('Observed Beam Angle (strongly recommend) ', validators = [Optional ()])
    reference = StringField('Reference', validators = [Optional ()])
    notes = StringField('Notes', validators = [Optional ()])
    submit = SubmitField('Submit')
