from __init__ import app, api_key, api_sec_key,db
from flask import render_template,flash, redirect,url_for, session, request,  send_file
from flask_login import current_user, login_user, login_required, logout_user
from __init__ import User, User_settings
from werkzeug.utils import secure_filename
import os

from forms import LoginForm, RegistrationForm, CustomizeForm
import tweepy

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
	if not os.path.exists(path_to_media):
		os.makedirs(path_to_media)
	f_names = [path_to_media+f for f in os.listdir(path_to_media)]

	usr_settings = User_settings.query.filter_by(user_id=user.id)
	if usr_settings.first():	
		form = CustomizeForm(obj=usr_settings.first().to_obj())
	else:
		form = CustomizeForm()
	if form.validate_on_submit():
		ids = " ".join(form.names.data.strip().split(' '))
		if usr_settings.first():
			usr_settings.update(dict(DM_reply_time=form.DM_reply_time.data,tweet_time=form.tweet_time.data,names=ids,questions=form.questions.data))
		else:
			new_settings = User_settings(user_id = user.id,DM_reply_time= form.DM_reply_time.data,tweet_time=form.tweet_time.data,names=ids,questions=form.questions.data)
			db.session.add(new_settings)
		db.session.commit()

		files = form.files.data
		if files[0].filename != "":
			for file in files:
				print(file)

				files_filenames = secure_filename(file.filename)
				print(files_filenames)
				file.save(os.path.join(path_to_media, files_filenames))
			
		
		return redirect(url_for('index'))
	return render_template('customize_bot.html',form=form,usernm=usernm,settings = usr_settings.first(),files = f_names,user_obj = user_obj)

@app.route('/index')
@login_required
def index():
    usernm = current_user.username
    user = User.query.filter_by(username=usernm).first()
    auth = tweepy.OAuthHandler(api_key,api_sec_key)
    auth.set_access_token(user.acc_token,user.acc_secret)
    api = tweepy.API(auth)
    user_obj = api.me()
    return render_template('index.html',usernm=usernm,user_obj=user_obj)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('customize_bot'))

@app.route('/media/<user_id>/<name>',methods=['GET','POST'])
def files(user_id,name):
	return send_file(app.config['UPLOAD_PATH']+user_id+'/'+name)

@app.route('/media/<user_id>/<name>/delete',methods=['GET','POST'])
def delete_file(user_id,name):
	filename = secure_filename(name)
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	path_to_media = app.config['UPLOAD_PATH']+str(user.id)+'/'
	path = os.path.join(path_to_media,filename)
	os.remove(path)
	flash("Image deleted")
	return redirect(url_for('customize_bot'))