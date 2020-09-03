from flask import Flask, session
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import logging

Base = declarative_base()

app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'
app.config['SECRET_KEY'] = "Everything will repeat"
app.config['UPLOAD_PATH'] = 'media/'
api_key = "kxNP9B8P5PoqTddS9bKkhQADd"
api_sec_key = "Asv6TgPPc5ONl6saKm8aAz9aIC4sKoVCEeJvBbUFUZKXTMlVbM"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

db = SQLAlchemy(app)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True



class User(UserMixin,db.Model):
	'''
		User database model
		username := twitter user name
		password_hash := password 
		acc_token := access token of the user
		acc_secret := access token secret of user
	'''
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	setting = db.relationship("User_settings",backref=backref("User_settings", uselist=False))
	username = db.Column(db.String(80), unique=True, nullable=False)
	password_hash = db.Column(db.String(128))
	acc_token = db.Column(db.String(), unique=True, nullable=False)
	acc_secret = db.Column(db.String(), unique=True, nullable=False)
	

	def __init__(self, username, acc_token,acc_secret):
		self.username = username
		self.acc_token = acc_token
		self.acc_secret = acc_secret

	def __repr__(self):
		return '<User %r>' % self.username

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

class User_settings(db.Model):
	"""
		User bot settings
	"""
	
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	user = relationship("User",backref=backref("user", uselist=False))
	DM_reply_time = db.Column(db.String(),nullable=False)
	tweet_time = db.Column(db.String(),unique=False,nullable=False)
	block_names = db.Column(db.String(),unique=False,nullable=True)
	sub_names = db.Column(db.String(),unique=False,nullable=True)
	questions_sub = db.Column(db.String(),nullable=True)
	questions_unsub = db.Column(db.String(),nullable=True)
	tweets = db.Column(db.String(),nullable=True)

	def __init__(self, user_id, DM_reply_time,tweet_time,block_names,sub_names,questions_sub,questions_unsub,tweets):
		self.user_id = user_id
		self.DM_reply_time = DM_reply_time
		self.tweet_time = tweet_time
		self.block_names = block_names
		self.sub_names = sub_names
		self.questions_sub = questions_sub
		self.questions_unsub = questions_unsub
		self.tweets = tweets
		
	def __repr__(self):
		return '<User %r>'%self.user_id

	def to_obj(self):
		class temp():
			DM_reply_time = self.DM_reply_time
			tweet_time = self.tweet_time
			files = None
			block_names = self.block_names
			sub_names = self.sub_names
			questions_sub = self.questions_sub
			questions_unsub = self.questions_unsub
			tweets = self.tweets
		return temp()
			
				


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
import views



