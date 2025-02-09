from __init__ import app, api_key, api_sec_key,db
from flask import render_template,flash, redirect,url_for, session, request,  send_file
from flask_login import current_user, login_user, login_required, logout_user
from __init__ import User, User_settings
from werkzeug.utils import secure_filename
import os
import threading
import time
from forms import LoginForm, RegistrationForm, CustomizeForm
import tweepy
import json
import cv2
from datetime import datetime
import logging
from PIL import Image, ImageFilter
from bot import Bot_tweet, Bot_reply, Bot_mention
from helper import GetDM

from TwitterAPI import TwitterAPI

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
	api = tweepy.API(auth,wait_on_rate_limit=True)
	user_obj = api.me()
	path_to_media = app.config['UPLOAD_PATH']+str(user.id)+'/'
	path_to_img = app.config['UPLOAD_PATH']+str(user.id)+'/img/'
	path_to_vid = app.config['UPLOAD_PATH']+str(user.id)+'/vid/'
	path_to_ls  = app.config['UPLOAD_PATH']+str(user.id)+'/ls_seen/'
	if not os.path.exists(path_to_media):
		os.makedirs(path_to_media)
		os.makedirs(path_to_img)
		os.makedirs(path_to_vid)
		os.makedirs(path_to_ls)
		f = open(app.config['UPLOAD_PATH']+str(user.id)+'/logs.log','w')
		f.close()
		f = open(app.config['UPLOAD_PATH']+str(user.id)+'/tasks.json','w')
		f.write("{}")
		f.close()
		file = open(path_to_ls+'last_seen.txt','w')
		file.close()
		file2 = open(path_to_ls+'msg_seen.txt','w')
		file2.close()
	i_names = [path_to_img+f for f in os.listdir(path_to_img)]
	v_names = [path_to_vid+f for f in os.listdir(path_to_vid)]
	usr_settings = User_settings.query.filter_by(user_id=user.id)
	if not usr_settings.first():
		new_settings = User_settings(user_id = user.id,DM_reply_time= "1",block_names="",sub_names="",questions_sub="",questions_unsub="")
		db.session.add(new_settings)
		db.session.commit()
	if usr_settings.first():	
		set_obj = usr_settings.first().to_obj()
		block_ids = []
		sub_ids = []

		for id_s in set_obj.block_names.split(' '):
			try:
				block_ids.append(api.get_user(id_s).screen_name)
			except:
				block_ids.append("")
		for id_s in set_obj.sub_names.split(' '):
			try:
				sub_ids.append(api.get_user(id_s).screen_name)
			except:
				sub_ids.append("")

		set_obj.block_names = " ".join([k for k in block_ids])
		set_obj.sub_names = " ".join([k for k in sub_ids])

		form = CustomizeForm(obj=set_obj)
	else:
		form = CustomizeForm()
	if form.validate_on_submit():
		block_ids = []
		sub_ids = []

		for sr_nm in form.block_names.data.strip().split(' '):
			try:
				block_ids.append(api.get_user(sr_nm).id_str)
			except:
				block_ids.append("")
		for sr_nm in form.sub_names.data.strip().split(' '):
			try:
				sub_ids.append(api.get_user(sr_nm).id_str)
			except:
				sub_ids.append("")

		block_ids = " ".join([k for k in block_ids])
		sub_ids = " ".join([k for k in sub_ids])
		if usr_settings.first():
			usr_settings.update(dict(DM_reply_time=form.DM_reply_time.data,block_names=block_ids,sub_names=sub_ids,questions_sub=form.questions_sub.data,questions_unsub=form.questions_unsub.data))
		else:
			new_settings = User_settings(user_id = user.id,DM_reply_time= form.DM_reply_time.data,block_names=block_ids,sub_names=sub_ids,questions_sub=form.questions_sub.data,questions_unsub=form.questions_unsub.data)
			db.session.add(new_settings)
		db.session.commit()

		files = form.files.data
		
		if files[0].filename != "":
			for file in files:
				files_filenames = secure_filename(file.filename)
				if any([files_filenames.lower().endswith(k) for k in ['png','jpg','jpeg']]):
					file.save(os.path.join(path_to_img, files_filenames))	
				elif any([files_filenames.lower().endswith(k) for k in ['mkv','mp4','gif','webm','mov']]):
					file.save(os.path.join(path_to_vid, files_filenames))
		
		return redirect(url_for('index'))
	return render_template('customize_bot.html',form=form,usernm=usernm,settings = usr_settings.first(),img_files = i_names, vid_files = v_names, user_obj = user_obj)

@app.route('/index/')
@app.route('/index')
def index():
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	auth = tweepy.OAuthHandler(api_key,api_sec_key)
	auth.set_access_token(user.acc_token,user.acc_secret)

	usr_settings = User_settings.query.filter_by(user_id=user.id).first()

	path_to_img = app.config['UPLOAD_PATH']+str(user.id)+'/img/'
	path_to_vid = app.config['UPLOAD_PATH']+str(user.id)+'/vid/'
	i_names = [path_to_img+f for f in os.listdir(path_to_img)]
	v_names = [path_to_vid+f for f in os.listdir(path_to_vid)]
	
	api = tweepy.API(auth,wait_on_rate_limit=True)
	user_obj = api.me()
	
	DM_df, sender_data = GetDM(api)
	if usr_settings:
		for s in sender_data:
			s['blocked'] = "Blocked" if s['id_str'] in usr_settings.block_names.split(" ") else "" 
			s['sub'] = "Subscribed user" if s['id_str'] in usr_settings.sub_names.split(" ") else ""
			
			s['days_since_reply'] = (datetime.now() - datetime.fromtimestamp(DM_df[DM_df['sender_id'] == s['id_str']]['timestamp'].values[0] / 1000)).days 

	tasks = json.load(open(app.config['UPLOAD_PATH']+str(user.id)+'/tasks.json'))		
	
	return render_template('index.html',user_obj=user_obj,im_files = i_names,v_files=v_names,tasks=tasks,DM_df=DM_df.to_json(),sender_data=sender_data)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('customize_bot'))

@app.route('/media/<user_id>/<f_type>/<name>',methods=['GET','POST'])
def files(user_id,f_type,name):
	return send_file(app.config['UPLOAD_PATH']+user_id+'/'+f_type+'/'+name)

@app.route('/media/<user_id>/<f_type>/<name>/blurrify',methods=['GET','POST'])
def blurrify(user_id,f_type,name):
	filename = secure_filename(name)
	path_to_media = app.config['UPLOAD_PATH']+str(user_id)+'/'+f_type+'/'	
	path = os.path.join(path_to_media,filename)
	if any([filename.lower().endswith(k) for k in ['png','jpg','jpeg']]):
		img = Image.open(path)
		b_img = img.filter(ImageFilter.BoxBlur(10))
		b_img.save(os.path.join(path_to_media,filename.split('.')[0]+'_premium.'+filename.split('.')[-1]))
	elif any([filename.lower().endswith(k) for k in ['mkv','mp4','webm','mov']]):
		cap = cv2.VideoCapture(path)
		codec_dict = {
		'.mp4':0x7634706d,
		'webm':cv2.VideoWriter_fourcc('w','e','b','m'),
		}
		if filename.split('.')[-1] == 'webm':
			fourcc =  cv2.VideoWriter_fourcc(*'VP90')
		else:
			fourcc = 0x7634706d
		res = cv2.VideoWriter(
			os.path.join(path_to_media,filename.split('.')[0]+'_premium.'+filename.split('.')[-1]),
			fourcc, 
            cap.get(cv2.CAP_PROP_FPS), (int(cap.get(3)), int(cap.get(4)))
			)
		while True:
			ret,  frame = cap.read()
			if ret:
				gray = cv2.GaussianBlur(frame, (11, 11), 0)
				res.write(gray)
			else:
				res.release()
				cap.release()
				cv2.destroyAllWindows()
				break
		cv2.destroyAllWindows() 

	return redirect(url_for('customize_bot'))

@app.route('/media/<user_id>/<f_type>/<name>/delete',methods=['GET','POST'])
def delete_file(user_id,f_type,name):
	filename = secure_filename(name)
	path_to_media = app.config['UPLOAD_PATH']+str(user_id)+'/'+f_type+'/'
	path = os.path.join(path_to_media,filename)
	os.remove(path)
	flash("Image deleted")
	return redirect(url_for('customize_bot'))


@app.route('/logs',methods=['GET','POST'])
def get_log():
	logs = []
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	with open(app.config['UPLOAD_PATH']+str(user.id)+'/logs.log','r') as f:
		for line in f.readlines():
			logs.append(line)
	return json.dumps(logs)



@app.route('/logs/clear',methods=['GET','POST'])
def log_clear():
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	with open(app.config['UPLOAD_PATH']+str(user.id)+'/logs.log','w') as f:
		f.truncate()
	return redirect(url_for('bot_logs'))



@app.route('/post/add',methods=['GET','POST'])
def post_add():
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	
	auth = tweepy.OAuthHandler(api_key,api_sec_key)
	auth.set_access_token(user.acc_token,user.acc_secret)
	api = tweepy.API(auth,wait_on_rate_limit=True)
	user_obj = api.me()

	api_vid = TwitterAPI(api_key,api_sec_key,user.acc_token,user.acc_secret)

	

	post = {}
	post['time'] = request.form.get('time_diff')
	post['media'] = request.form.get('media')
	post['text'] = request.form.get('tweet_txt')

	tasks = json.load(open(app.config['UPLOAD_PATH']+str(user.id)+'/tasks.json'))
	post['id'] = str(len(tasks))
	
	bot_tw = Bot_tweet(name=usernm,api=api,uid = user.id,api_vid = api_vid, post = post)
	bot_tw.start()

	post['time'] = request.form.get('time')
	tasks[str(len(tasks))] = post
	json.dump(tasks,open(app.config['UPLOAD_PATH']+str(user.id)+'/tasks.json','w'))

	
	logging.info("Tweet post created will tweet in "+str(request.form.get('time_diff'))+" seconds.")

	return redirect(url_for('index'))

@app.route('/bot_logs',methods=['GET','POST'])
@app.route('/bot_logs/<command>')
@login_required
def bot_logs(command=None):
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	auth = tweepy.OAuthHandler(api_key,api_sec_key)
	auth.set_access_token(user.acc_token,user.acc_secret)

	api = tweepy.API(auth,wait_on_rate_limit=True)

	api_vid = TwitterAPI(api_key,api_sec_key,user.acc_token,user.acc_secret)

	user_obj = api.me()

	filehandler = logging.FileHandler(app.config['UPLOAD_PATH']+str(user.id)+'/logs.log', 'a')
	log = logging.getLogger()
	for hdlr in log.handlers[:]:
		if isinstance(hdlr,logging.FileHandler):
			log.removeHandler(hdlr)
	log.addHandler(filehandler) 

	main_th = threading.current_thread()
	bot_status = False
	for t in threading.enumerate():
		if t is main_th:
			continue
		elif t.getName()  == usernm:
			bot_status = True

	if command == 'activate':		
		bot_status = True
		bot_men = Bot_mention(name=usernm,api=api,uid = user.id)
		bot_re = Bot_reply(name=usernm,api=api,uid = user.id,api_vid=api_vid)
		bot_men.start()
		bot_re.start()
		logging.info("Bot started")
		db.session.commit()

	elif command == 'deactivate':
		bot_status = False
		logging.info("stopping Bot")
		for t in threading.enumerate():
			if t is main_th:
				continue
			elif t.getName()  == usernm:
				t.raise_exception()
		for t in threading.enumerate():
			print(t.getName())

	return render_template('bot_logs.html',user_obj=user_obj,bot_status=bot_status)


@app.route('/block/<usr_id>')
@login_required
def bolck_usr(usr_id=None):
	usernm = current_user.username
	user = User.query.filter_by(username=usernm).first()
	usr_settings = User_settings.query.filter_by(user_id=user.id)
	block_names = usr_settings.first().block_names.split(' ')
	block_names.append(usr_id)
	usr_settings.update(dict(block_names=" ".join(block_names)))
	db.session.commit()
	return redirect(url_for('index'))






