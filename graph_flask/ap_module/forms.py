from wtforms import StringField, PasswordField, SubmitField,  RadioField, BooleanField, DecimalField, FileField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_wtf import FlaskForm
from graph_flask.models import form_list,strata_roll
import re

class Agm_list_form(FlaskForm):

    File_uploaded = FileField('File_uploaded')
    submit = SubmitField('Upload')


class sample_form(FlaskForm):
    choices = [(1, 'Attending in person'), (2, 'Transfer voting rights to another owned unit'),(3, 'Transfer voting rights to proxy')]
    Mcst = StringField('Mcst', validators=[DataRequired()])
    full_name = StringField('Name of Subsidiary Proprietors', validators=[DataRequired()])
    contact_no = StringField('contact_no ',validators=[DataRequired()])
    date_registered = DateField('date_registered ', format= '%Y-%m-%d')
    email = StringField('email ', validators=[Email(),Optional()])
    blk = StringField('blk no ',validators=[DataRequired()])
    floor = StringField('level ',validators=[DataRequired()])
    unit_no = StringField('unit ',validators=[DataRequired()])
    unit =  StringField('email ', validators=[])
    attending = RadioField('attending', validators=[], choices=choices, default="0", coerce=int)
    submit = SubmitField('Submit Survey')

    def validate_blk(self ,blk):

        register_unit = self.combine_unit_no()
        print(register_unit)
        valid_unit = form_list.query.filter_by(unit=register_unit).first()

        if valid_unit:
            raise ValidationError('The Unit had registered and submitted vote ')

        strata_list = strata_roll.query.filter(strata_roll.MCST_id == self.Mcst.data).filter(strata_roll.unit_account == register_unit).first()

        if not strata_list:
            raise ValidationError('Invalid Blk and Unit No. Please check input')

    def combine_unit_no(self):

        self.blk.data = re.sub(r'\D+','',str(self.blk.data))
        self.unit_no.data = re.sub(r'\D+', '', str(self.unit_no.data))
        self.floor.data = re.sub(r'\D+', '', str(self.floor.data))

        unit = f'{int(self.blk.data):03d}-{int(self.floor.data):02d}-{int(self.unit_no.data):02d}'

        return unit


