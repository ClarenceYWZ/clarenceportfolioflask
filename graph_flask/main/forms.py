from wtforms import StringField, PasswordField, SubmitField,  RadioField, BooleanField, DecimalField, FileField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_wtf import FlaskForm

class Agm_list_form(FlaskForm):

    File_uploaded = FileField('File_uploaded')
    submit = SubmitField('Upload')
