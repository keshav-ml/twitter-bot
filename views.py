from __init__ import app, api_key, api_sec_key,db
from flask import render_template,flash, redirect,url_for, session, request,  send_file
from flask_login import current_user, login_user, login_required, logout_user
from __init__ import User, User_settings
from werkzeug.utils import secure_filename
import os
import threading
import time
import pandas as pd
import numpy as np
from forms import LoginForm, RegistrationForm, CustomizeForm
import tweepy
from filetype import guess
import logging
from bot import Bot

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

@app.route("/",methods=['POST','GET'])
@app.route("/login",methods=['POST','GET'])
def login():

	if current_user.is_authenticated:
		return redirect(url_for('customize_bot'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		return redirect(url_for('customize_bot'))
	return render_template('login.html', title='Log In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('customize_bot'))
    form = RegistrationForm()
    auth = tweepy.OAuthHandler(api_key,api_sec_key)
    if form.validate_on_submit():
    	session['username'] = form.username.data
    	session['password'] = form.password.data
    	flash("redirecting to Twitter")
    	return redirect(auth.get_authorization_url())
    	
    oauth_t = request.args.get('oauth_token')
    oauth_v = request.args.get('oauth_verifier')
    if oauth_t:
    	auth.request_token = { 'oauth_token' : oauth_t,'oauth_token_secret' : oauth_v }
    	auth.get_access_token(oauth_v)
    	user = User(username=session['username'],acc_token= auth.access_token,acc_secret=auth.access_token_secret)
    	user.set_password(session['password'])
    	db.session.add(user)
    	db.session.commit()
    	flash('Congratulations, you are now a registered user!')
    	return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/customize_bot',methods=['POST','GET'])
@login_required
def customize_bot():	
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	auth = tweepy.OAuthHandler(api_key,api_sec_key)
	auth.set_access_token(user.acc_token,user.acc_secret)
	api = tweepy.API(auth)
	user_obj = api.me()
	path_to_media = app.config['UPLOAD_PATH']+str(user.id)+'/'
	path_to_img = app.config['UPLOAD_PATH']+str(user.id)+'/img/'
	path_to_vid = app.config['UPLOAD_PATH']+str(user.id)+'/vid/'
	if not os.path.exists(path_to_media):
		os.makedirs(path_to_media)
		os.makedirs(path_to_img)
		os.makedirs(path_to_vid)
	f_names = [path_to_img+f for f in os.listdir(path_to_img)]
	f_names.extend([path_to_vid+f for f in os.listdir(path_to_vid)])
	usr_settings = User_settings.query.filter_by(user_id=user.id)
	if usr_settings.first():	
		form = CustomizeForm(obj=usr_settings.first().to_obj())
	else:
		form = CustomizeForm()
	if form.validate_on_submit():

		ids = " ".join(form.names.data.strip().split(' '))

		if usr_settings.first():
			usr_settings.update(dict(DM_reply_time=form.DM_reply_time.data,tweet_time=form.tweet_time.data,names=ids,questions=form.questions.data,tweets=form.tweets.data))
		else:
			new_settings = User_settings(user_id = user.id,DM_reply_time= form.DM_reply_time.data,tweet_time=form.tweet_time.data,names=ids,questions=form.questions.data,tweets=form.tweets.data)
			db.session.add(new_settings)
		db.session.commit()

		files = form.files.data
		
		if files[0].filename != "":
			for file in files:
				f_type = guess(file)
				files_filenames = secure_filename(file.filename)
				if f_type.mime.split('/')[0] == 'image':
					file.save(os.path.join(path_to_img, files_filenames))
					f_names.append(os.path.join(path_to_img, file.filename))
				elif f_type.mime.split('/')[0] == 'video':
					file.save(os.path.join(path_to_vid, files_filenames))
					f_names.append(os.path.join(path_to_vid, file.filename))


				
				
			
		
		return redirect(url_for('index'))
	return render_template('customize_bot.html',form=form,usernm=usernm,settings = usr_settings.first(),files = f_names,user_obj = user_obj)

@app.route('/index')
@app.route('/index/<command>')
@login_required
def index(command=None):
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	auth = tweepy.OAuthHandler(api_key,api_sec_key)
	auth.set_access_token(user.acc_token,user.acc_secret)
	filename  = app.config['UPLOAD_PATH']+str(user.id)+'/ls_seen/'
	if not os.path.exists(filename):
		os.makedirs(filename)
		file = open(filename+'last_seen.txt','w')
		file.close()
		file2 = open(filename+'msg_seen.txt','w')
		file2.close()
	
	api = tweepy.API(auth)
	user_obj = api.me()
	stop_eve = threading.Event()
	main_th = threading.current_thread()
	bot_status = False
	for t in threading.enumerate():
		if t is main_th:
			continue
		elif t.getName()  == usernm:
			bot_status = True

	if command == 'activate':		
		bot_status = True
		logging.info("Thread created")
		bot = Bot(name=usernm,api=api,uid = user.id)		
		bot.start()
		logging.info("Threads started")
		db.session.commit()

	elif command == 'deactivate':
		bot_status = False
		logging.info("stopping thread")
		logging.info("Thread stoped")
		for t in threading.enumerate():
			print(t.getName())
			if t is main_th:
				continue
			elif t.getName()  == usernm:
				t.raise_exception()
	

	return render_template('index.html',user_obj=user_obj,bot_status=bot_status)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('customize_bot'))

@app.route('/media/<user_id>/<f_type>/<name>',methods=['GET','POST'])
def files(user_id,f_type,name):
	return send_file(app.config['UPLOAD_PATH']+user_id+'/'+f_type+'/'+name)

@app.route('/media/<user_id>/<f_type>/<name>/delete',methods=['GET','POST'])
def delete_file(user_id,f_type,name):
	filename = secure_filename(name)
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	path_to_media = app.config['UPLOAD_PATH']+str(user.id)+'/'+f_type+'/'
	path = os.path.join(path_to_media,filename)
	os.remove(path)
	flash("Image deleted")
	return redirect(url_for('customize_bot'))