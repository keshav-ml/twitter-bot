from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, MultipleFileField, TextAreaField

from wtforms.validators import ValidationError, DataRequired, EqualTo
from __init__ import User



class LoginForm(FlaskForm):
	"""
	Login Class for creating login form 

	username : For getting username
	password : For password
	remember me : for boolean input
	submit : submit Button

	"""
	username = StringField("Username",validators=[DataRequired()])
	password = PasswordField("Password",validators=[DataRequired()])
	remember_me = BooleanField("Remember Me")
	submit = SubmitField("Log In")

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')


class CustomizeForm(FlaskForm):
	DM_reply_time = StringField("Dm reply time", validators=[DataRequired()])
	files = MultipleFileField("Selelct files for bot to use.")
	block_names = TextAreaField("Enter twitter id names, that bot will not reply.")
	sub_names = TextAreaField("Enter subscribed users.")
	questions_sub = StringField()
	questions_unsub = StringField()
	submit = SubmitField('Save')		

		
		