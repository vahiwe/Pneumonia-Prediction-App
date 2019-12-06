from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, RadioField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class 
from flask_wtf.file import FileField, FileRequired, FileAllowed
from app.models import User

photos = UploadSet('photos', IMAGES)


class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Change Password')

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[
                        DataRequired(), Email(), Length(min=6, max=40)])
    submit = SubmitField('Send Reset Email')
class UploadForm(FlaskForm):
    patient = StringField(u'Patient Name:')
    photo = FileField(validators=[FileAllowed(photos, 'Image Only!'), FileRequired('Choose a file!')])
    submit = SubmitField('Upload')

class LoginForm(FlaskForm):
    email = StringField(u'Email:', validators=[DataRequired(), Email(), Length(min=6,max=40)])
    password = PasswordField(u'Password:', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    firstname = StringField(u'Firstname:', validators=[DataRequired()])
    lastname = StringField(u'Lastname:', validators=[DataRequired()])
    email = StringField(u'Email:', validators=[DataRequired(), Email()])
    password = PasswordField(u'Password:', validators=[DataRequired(), Length(min=8, max=40)])
    password2 = PasswordField(
        u'Confirm Password:', validators=[DataRequired(), EqualTo('password', message="This should be equal to the new password")])
    gender = RadioField(u'Gender:', validators=[DataRequired()], choices=[('Male','Male'),('Female','Female')] )
    profession = SelectField(u'Profession', validators=[DataRequired()], choices=[
                             ('Medical Doctor', 'Medical Doctor'), ('Nurse', 'Nurse'), ('Radiologist','Radiologist')], default=[('Medical Doctor','Medical Doctor')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(
        photos, 'Image Only!')])
    firstname = StringField(u'Firstname:',validators=[DataRequired()])
    lastname = StringField(u'Lastname:', validators=[DataRequired()])
    email = StringField(u'Email:')
    gender = RadioField(u'Gender:', validators=[DataRequired()], choices=[('Male', 'Male'), ('Female', 'Female')])
    profession = SelectField(u'Profession', validators=[DataRequired()], choices=[
                             ('Medical Doctor', 'Medical Doctor'), ('Nurse', 'Nurse'), ('Radiologist','Radiologist')])
    submit = SubmitField('Save')

    # def __init__(self, original_email, *args, **kwargs):
    #     super(EditProfileForm, self).__init__(*args, **kwargs)
    #     self.original_email = original_email

    # def validate_username(self, email):
    #     if email.data != self.original_email:
    #         user = User.query.filter_by(email=self.email.data).first()
    #         if user is not None:
    #             raise ValidationError('Please use a different username.')

class PasswordChangeForm(FlaskForm):
    password = PasswordField(u'Old Password:', validators=[DataRequired(), Length(min=8, max=40)])
    password2 = PasswordField(u'New Password:', validators=[
                              DataRequired(), Length(min=8, max=40)])
    password3 = PasswordField(u'Confirm New Password:', validators=[
                              DataRequired(), EqualTo('password2',message="This should be equal to the new password"), Length(min=8, max=40)])
    submit = SubmitField('Update')
