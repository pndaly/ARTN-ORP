#!/usr/bin/env python3.7


# +
# import(s)
# -
from src import *
from src.models.Models import User
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField
from wtforms import DateTimeField
from wtforms import FloatField
from wtforms import IntegerField
from wtforms import PasswordField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import NumberRange
from wtforms.validators import Regexp
from wtforms.validators import Length
from wtforms.validators import ValidationError


# +
# constant(s)
# -
AIRMASS_DEFAULT = 2.0
AIRMASS_MIN = 1.0
AIRMASS_MAX = 3.5
BINNING = [('4x4', '4x4'), ('3x3', '3x3'), ('2x2', '2x2'), ('None', 'None')]
CADENCE = [('Once', 'Once'), ('Daily', 'Daily'), ('BisInDie', 'BisInDie'),
           ('Weekly', 'Weekly'), ('Monthly', 'Monthly')]
CATEGORY = [('Bug', 'Bug'), ('Feature', 'Feature'), ('Enhancement', 'Enhancement'),
            ('Compliment', 'Compliment'), ('Other', 'Other')]
DEC_DEFAULT = 0.0
DEC_MIN = -90.0
DEC_MAX = 90.0
DITHER = [('None', 'None'), ('n-RA', 'n-RA'), ('n-Dec', 'n-Dec'), ('NxM', 'NxM')]
EXP_TIME_DEFAULT = 30.0
EXP_TIME_MIN = 0.0
EXP_TIME_MAX = 1800.0
FILTER_NAMES = [('U', 'U'), ('B', 'B'), ('V', 'V'), ('R', 'R'), ('I', 'I'), ('Clear', 'Clear')]
LOOKBACK_PERIOD = [('30', '30 Days'), ('60', '60 Days'),
                   ('90', '90 Days'), ('180', '180 Days'), ('365', '365 Days')]
LUNARPHASE = [('Dark', 'Dark'), ('Grey', 'Grey'), ('Bright', 'Bright'), ('mBright', 'mBright'), ('Any', 'Any')]
OBSERVATION_TYPES = [('all', 'All'), ('bias', 'Bias'), ('calibration', 'Calibration'), ('dark', 'Dark'), 
                     ('flat', 'Flat'), ('focus', 'Focus'), ('object', 'Object'), ('skyflat', 'SkyFlat'), 
                     ('standard', 'Standard')]
OLD_OBSERVATION_TYPES = [('all', 'All'), ('darks', 'Darks'), ('flats', 'Flats'), ('focus', 'Focus'),
                     ('objects', 'Objects'), ('skyflats', 'SkyFlats')]
PRIORITY = [('Routine', 'Routine'), ('Urgent', 'Urgent')]
QUALITY = [('None', 'None'), ('S/N>10', 'S/N>10')]
MOON_DEFAULT = 1.0
MOON_MIN = -15.0
MOON_MAX = 15.0
NUM_EXP_DEFAULT = 1
NUM_EXP_MIN = 1
NUM_EXP_MAX = 500
NS_DEFAULT = '{"RA_BiasRate": "0.0", "Dec_BiasRate": "0.0", "ObjectRate": "0.0", ' \
             '"PositionAngle": "0.0", "UTC_At_Position": "YYYY-MM-DDThh:mm:ss.s"}'
RA_DEFAULT = 0.0
RA_MIN = 0.0
RA_MAX = 24.0
URGENCY = [('Routine', 'Routine'), ('Urgent', 'Urgent'), ('Critical', 'Critical')]

FORM_TELESCOPES = [('Bok', 'Bok 90-inch'), ('Kuiper', 'Kuiper 61-inch'), ('MMT', 'MMT 6.5m'), ('Vatt', 'Vatt 1.8m')]
FORM_INSTRUMENTS = [('90Prime', '90Prime'), ('BCSpec', 'BCSpec'), ('Mont4k', 'Mont4k'), ('BinoSpec', 'BinoSpec'), ('Vatt4k', 'Vatt4k')]

RA_BIASRATE_DEFAULT = 0.0
RA_BIASRATE_MIN = -50.0
RA_BIASRATE_MAX = 50.0

RA_PERCENT_DEFAULT = 50.0
RA_PERCENT_MIN = 0.0
RA_PERCENT_MAX = 100.0

DEC_BIASRATE_DEFAULT = 0.0
DEC_BIASRATE_MIN = -50.0
DEC_BIASRATE_MAX = 50.0

DEC_PERCENT_DEFAULT = 50.0
DEC_PERCENT_MIN = 0.0
DEC_PERCENT_MAX = 100.0

PA_DEFAULT = 0.0
PA_MIN = 0.0
PA_MAX = 360.0


# +
# scope variable(s)
# -
regexp_ra = re.compile(ARTN_RA_PATTERN)
regexp_dec = re.compile(ARTN_DEC_PATTERN)


# +
# class: ConfirmDeleteForm(), inherits from FlaskForm
# -
class ConfirmDeleteForm(FlaskForm):

    # submit
    submit = SubmitField('OK')


# +
# class: ConfirmRegistrationForm(), inherits from FlaskForm
# -
class ConfirmRegistrationForm(FlaskForm):

    # fields
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    affiliation = StringField('Affiliation', validators=[DataRequired()])
    is_disabled = BooleanField('Is Disabled?')

    # submit
    submit = SubmitField('Confirm Registration')


# +
# class: FeedbackForm(), inherits from FlaskForm
# -
class FeedbackForm(FlaskForm):

    # fields
    category = SelectField('Category', choices=CATEGORY, default=CATEGORY[0][0], validators=[DataRequired()])
    urgency = SelectField('Urgency', choices=URGENCY, default=URGENCY[0][0], validators=[DataRequired()])
    report = TextAreaField('Report', validators=[Length(min=0, max=ARTN_CHAR_256)])
    screenshot = FileField('Screenshot')

    # submit
    submit = SubmitField('Submit Feedback')


# +
# class: LoginForm(), inherits from FlaskForm
# -
class LoginForm(FlaskForm):

    # fields
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

    # submit
    submit = SubmitField('Login')


# +
# class: ObsReqForm(), inherits from FlaskForm
# -
class ObsReqForm(FlaskForm):

    # fields
    # username = SelectField('Username', choices=USERS, default=USERS[0][0], validators=[DataRequired()])
    username = StringField('Username', default='')
    priority = SelectField('Priority', choices=PRIORITY, default=PRIORITY[0][0], validators=[DataRequired()])
    object_name = StringField('Object Name', default='', validators=[DataRequired()])
    ra_hms = StringField('RA', default='', validators=[
        DataRequired(), Regexp(regex=regexp_ra, flags=re.IGNORECASE, message='RA format is HH:MM:SS.S')])
    dec_dms = StringField('Dec', default='', validators=[
        DataRequired(), Regexp(regex=regexp_dec, flags=re.IGNORECASE, message='Dec format is +/-dd:mm:ss.s')])
    begin_iso = DateTimeField('UTC Begin DateTime', default=get_date_utctime(), format='%Y-%m-%d %H:%M:%S',
                              validators=[DataRequired()])
    end_iso = DateTimeField('UTC End DateTime', default=get_date_utctime(30), format='%Y-%m-%d %H:%M:%S',
                            validators=[DataRequired()])
    airmass = FloatField('Airmass Maximum', default=AIRMASS_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=AIRMASS_MIN, max=AIRMASS_MAX, message=f'{AIRMASS_MIN} < airmass < {AIRMASS_MAX}')])
    lunarphase = SelectField('Lunar Phase', choices=LUNARPHASE, default=LUNARPHASE[0][0], validators=[DataRequired()])
    photometric = BooleanField('Photometric', false_values=(False, 'false', 0, '0'), default=False)
    guiding = BooleanField('Guiding', false_values=(False, 'false', 0, '0'), default=False)
    non_sidereal = BooleanField('Non-Sidereal', false_values=(False, 'false', 0, '0'), default=False)
    filter_name = SelectField(choices=FILTER_NAMES, default=FILTER_NAMES[0][0], validators=[DataRequired()])
    exp_time = FloatField('Exposure Time', default=EXP_TIME_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=EXP_TIME_MIN, max=EXP_TIME_MAX, message=f'{EXP_TIME_MIN} < exposure time < {EXP_TIME_MAX}')])
    num_exp = IntegerField('# Exposures', default=NUM_EXP_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=NUM_EXP_MIN, max=NUM_EXP_MAX, message=f'{NUM_EXP_MIN} < # exposures < {NUM_EXP_MAX}')])
    binning = SelectField('Binning', choices=BINNING, default=BINNING[0][0], validators=[DataRequired()])
    dither = SelectField('Dither', choices=DITHER, default=DITHER[0][0], validators=[DataRequired()])
    cadence = SelectField('Cadence', choices=CADENCE, default=CADENCE[0][0], validators=[DataRequired()])
    telescope = SelectField('Telescope', choices=FORM_TELESCOPES, default=FORM_TELESCOPES[1][1], validators=[DataRequired()])
    instrument = SelectField('Instrument', choices=FORM_INSTRUMENTS, default=FORM_INSTRUMENTS[2][1], validators=[DataRequired()])

    # non-sidereal widgets
    ns_params = StringField('Non-Sidereal Parameter(s)', default=NS_DEFAULT, validators=[DataRequired()])

    # submit
    submit = SubmitField('Create Observation Request')


# +
# class: ProfileForm(), inherits from FlaskForm
# -
class ProfileForm(FlaskForm):

    # fields
    email = StringField('Email', validators=[DataRequired(), Email()])
    about_me = TextAreaField('About Me', validators=[Length(min=0, max=ARTN_CHAR_256)])
    affiliation = StringField('Affiliation', validators=[DataRequired(), Length(min=0, max=ARTN_CHAR_256)])
    avatar = StringField('Avatar', validators=[DataRequired()])

    # submit
    submit = SubmitField('Submit')


# +
# class: RegistrationForm(), inherits from FlaskForm
# -
class RegistrationForm(FlaskForm):

    # fields
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    affiliation = StringField('Affiliation', validators=[DataRequired()])
    password = PasswordField(
        'Password', validators=[DataRequired(), EqualTo('confirm', message='Passwords must match'),
                                Length(min=8, message='Minimum 8 characters')])
    confirm = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    passphrase = StringField('Pass Phrase', validators=[DataRequired()])
    policy_ok = BooleanField('I agree to the', validators=[DataRequired()])

    # submit
    submit = SubmitField('Register')

    # +
    # method: validate_username()
    # -
    # noinspection PyMethodMayBeStatic
    def validate_username(self, username=None):
        if username is None:
            raise ValidationError('Invalid input argument')
        _u = User.query.filter_by(username=self.username.data).first()
        if _u is not None:
            raise ValidationError('Please use a different username')

    # +
    # method: validate_email()
    # -
    # noinspection PyMethodMayBeStatic
    def validate_email(self, email=None):
        if email is None:
            raise ValidationError('Invalid input argument')
        _u = User.query.filter_by(email=self.email.data).first()
        if _u is not None:
            raise ValidationError('Please use a different email address')


# +
# class: ResetPasswordForm(), inherits from FlaskForm
# -
class ResetPasswordForm(FlaskForm):

    # field(s)
    password = PasswordField('Password', validators=[
        DataRequired(),
        EqualTo('confirm', message='Passwords must match'), Length(min=6, message='Minimum 6 characters')])
    confirm = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')])

    # submit
    submit = SubmitField('Request Password Reset')


# +
# class: ResetPasswordRequestForm(), inherits from FlaskForm
# -
class ResetPasswordRequestForm(FlaskForm):

    # fields
    email = StringField('Email', validators=[DataRequired(), Email()])
    passphrase = StringField('Pass Phrase', validators=[DataRequired()])

    # submit
    submit = SubmitField('Request Password Reset')


# +
# class: UpdateObsReqForm(), inherits from FlaskForm
# -
class UpdateObsReqForm(FlaskForm):

    # fields
    # username = StringField('Username', default='', validators=[DataRequired()])
    username = StringField('Username', default='')
    priority = SelectField('Priority', choices=PRIORITY, default=PRIORITY[0][0], validators=[DataRequired()])
    object_name = StringField('Object Name', default='', validators=[DataRequired()])
    ra_hms = StringField('RA', default='', validators=[
        DataRequired(), Regexp(regex=regexp_ra, flags=re.IGNORECASE, message='RA format is HH:MM:SS.S')])
    dec_dms = StringField('Dec', default='', validators=[
        DataRequired(), Regexp(regex=regexp_dec, flags=re.IGNORECASE, message='Dec format is +/-dd:mm:ss.s')])
    begin_iso = DateTimeField('UTC Begin DateTime', default=get_date_utctime(), format='%Y-%m-%d %H:%M:%S', validators=[
        DataRequired()])
    end_iso = DateTimeField('UTC End DateTime', default=get_date_utctime(30), format='%Y-%m-%d %H:%M:%S', validators=[
        DataRequired()])
    airmass = FloatField('Airmass', default=AIRMASS_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=AIRMASS_MIN, max=AIRMASS_MAX, message=f'{AIRMASS_MIN} < airmass < {AIRMASS_MAX}')])
    lunarphase = SelectField('Lunar Phase', choices=LUNARPHASE, default=LUNARPHASE[0][0], validators=[DataRequired()])
    photometric = BooleanField('Photometric', false_values=(False, 'false', 0, '0'), default=False)
    guiding = BooleanField('Guiding', false_values=(False, 'false', 0, '0'), default=False)
    non_sidereal = BooleanField('Non-Sidereal', false_values=(False, 'false', 0, '0'), default=False)
    filter_name = SelectField(choices=FILTER_NAMES, default=FILTER_NAMES[0][0], validators=[DataRequired()])
    exp_time = FloatField('Exposure Time', default=EXP_TIME_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=EXP_TIME_MIN, max=EXP_TIME_MAX, message=f'{EXP_TIME_MIN} < exposure time < {EXP_TIME_MAX}')])
    num_exp = IntegerField('# Exposures', default=NUM_EXP_DEFAULT, validators=[
        DataRequired(),
        NumberRange(min=NUM_EXP_MIN, max=NUM_EXP_MAX, message=f'{NUM_EXP_MIN} < # exposures < {NUM_EXP_MAX}')])
    binning = SelectField('Binning', choices=BINNING, default=BINNING[0][0], validators=[DataRequired()])
    dither = SelectField('Dither', choices=DITHER, default=DITHER[0][0], validators=[DataRequired()])
    cadence = SelectField('Cadence', choices=CADENCE, default=CADENCE[0][0], validators=[DataRequired()])
    telescope = SelectField('Telescope', choices=FORM_TELESCOPES, default=FORM_TELESCOPES[1][1], validators=[DataRequired()])
    instrument = SelectField('Instrument', choices=FORM_INSTRUMENTS, default=FORM_INSTRUMENTS[2][1], validators=[DataRequired()])

    # non-sidereal widgets
    ns_params = StringField('Non-Sidereal Parameter(s)', default=NS_DEFAULT, validators=[DataRequired()])

    # submit
    submit = SubmitField('Update Observation Request')


# +
# class: UploadForm(), inherits from FlaskForm
# -
class UploadForm(FlaskForm):

    # fields
    filename = FileField('Filename', validators=[FileRequired(), FileAllowed(['csv', 'tsv'], 'CSV or TSV only!')])

    # submit
    submit = SubmitField('Upload File')


# +
# class: UserHistoryForm(), inherits from FlaskForm
# -
class UserHistoryForm(FlaskForm):

    # fields
    instrument = SelectField('Instrument', choices=FORM_INSTRUMENTS, default=FORM_INSTRUMENTS[2][1], validators=[DataRequired()])
    lookback = SelectField('Lookback Period', choices=LOOKBACK_PERIOD,
                           default=LOOKBACK_PERIOD[0][0], validators=[DataRequired()])
    telescope = SelectField('Telescope', choices=FORM_TELESCOPES, default=FORM_TELESCOPES[1][1], validators=[DataRequired()])
    username = StringField('Username', default='')

    # submit
    submit = SubmitField('Submit')


# +
# class: OldNightLogForm(), inherits from FlaskForm
# -
class OldNightLogForm(FlaskForm):

    # fields
    telescope = SelectField('Telescope', choices=FORM_TELESCOPES, default=FORM_TELESCOPES[1][1], validators=[DataRequired()])
    obs = SelectField('Observation Type', choices=OLD_OBSERVATION_TYPES,
                      default=OLD_OBSERVATION_TYPES[0][0], validators=[DataRequired()])
    iso = DateTimeField('Date', default=get_date_time(), format='%Y-%m-%d', validators=[DataRequired()])
    pdf = BooleanField('Generate PDF', false_values=(False, 'false', 0, '0'), default=False)

    # submit
    submit = SubmitField('Submit')

    # validator for iso field
    # noinspection PyUnusedLocal
    @staticmethod
    def validate_iso(form, field):

        _today = get_date_time(0)
        if iso_to_jd(field.data) > iso_to_jd(_today):
            raise ValidationError("Observation date must not be in the future!")

        _year_ago = get_date_time(-ARTN_LOOKBACK_PERIOD)
        if iso_to_jd(field.data) < iso_to_jd(_year_ago):
            raise ValidationError("Observation date must be in the last year!")


# +
# class: NightLogForm(), inherits from FlaskForm
# -
class NightLogForm(FlaskForm):

    # fields
    instrument = SelectField('Instrument', choices=FORM_INSTRUMENTS, default=FORM_INSTRUMENTS[2][1], validators=[DataRequired()])
    iso = DateTimeField('Date', default=get_date_time(), format='%Y-%m-%d', validators=[DataRequired()])
    obs = SelectField('Observation Type', choices=OBSERVATION_TYPES,
                      default=OBSERVATION_TYPES[0][0], validators=[DataRequired()])
    pdf = BooleanField('Generate PDF', false_values=(False, 'false', 0, '0'), default=False)
    telescope = SelectField('Telescope', choices=FORM_TELESCOPES, default=FORM_TELESCOPES[1][1], validators=[DataRequired()])

    # submit
    submit = SubmitField('Submit')

    # validator for iso field
    # noinspection PyUnusedLocal
    @staticmethod
    def validate_iso(form, field):

        _today = get_date_time(0)
        if iso_to_jd(field.data) > iso_to_jd(_today):
            raise ValidationError("Observation date must not be in the future!")

        _year_ago = get_date_time(-ARTN_LOOKBACK_PERIOD)
        if iso_to_jd(field.data) < iso_to_jd(_year_ago):
            raise ValidationError("Observation date must be in the last year!")
