import tweepy
import time
import random
import json
from __init__ import app
import threading
from __init__ import db, User_settings, User
import logging
import textdistance as td
import os
import ctypes

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

class Bot_tweet(threading.Thread):
        
	def __init__(self, name,api,uid,post):
		threading.Thread.__init__(self,name=name) 
		self.api = api
		self.uid = uid
		self.post = post
		filehandler = logging.FileHandler(app.config['UPLOAD_PATH']+str(uid)+'/logs.log', 'a')
		log = logging.getLogger()
		for hdlr in log.handlers[:]:
			if isinstance(hdlr,logging.FileHandler): 
				log.removeHandler(hdlr)
		log.addHandler(filehandler)

	def run(self):
		try:
			'''logging.info("Tweet thread running")
			while True:		
				user_set = User_settings.query.filter_by(user_id=self.uid).first()
				tweets = json.loads(user_set.tweets)
				if len(tweets) == 0:
					logging.info("No tweet found in settings skipping tweet")
					return 
				rand_int = random.randint(0,len(tweets)-1)
				files = ['media/'+str(self.uid)+'/img/'+v for v in os.listdir('media/'+str(self.uid)+'/img/')]
				rand_file = random.randint(0,len(files)-1)
				if random.randint(0,10) % 2 == 0:
					med = self.api.media_upload(filename  = files[rand_file])
					self.api.update_status(tweets[rand_int],media_ids=[med.media_id])
					logging.info("tweeted with media")
				else:
					self.api.update_status(tweets[rand_int])
					logging.info("tweeted without media")
				print(user_set.tweet_time)
				time.sleep(int(user_set.tweet_time))'''
			
			path_to_im = app.config['UPLOAD_PATH']+str(self.uid)+'/img/'
			path_to_v = app.config['UPLOAD_PATH']+str(self.uid)+'/vid/'
			time.sleep(int(self.post['time']))
			
			if self.post['media']:
				if any([self.post['media'].lower().endswith(k) for k in ['png','jpg','jpeg']]):
					med = self.api.media_upload(filename=path_to_im+self.post['media'])
				else:
					med = self.api.media_upload(filename=path_to_v+self.post['media'])
				
				self.api.update_status(self.post['text'],media_ids=[med.media_id])

			else:
				self.api.update_status(self.post['text'])

		finally:
			tasks = json.load(open(app.config['UPLOAD_PATH']+str(self.uid)+'/tasks.json'))
			del tasks[self.post['id']]
			json.dump(tasks,open(app.config['UPLOAD_PATH']+str(self.uid)+'/tasks.json','w'))
			logging.info("Tweeted")


	def get_id(self):
		if hasattr(self, '_thread_id'):
			return self._thread_id
		for id, thread in threading._active.items():
			if thread is self:
				return id

	def raise_exception(self):
		thread_id = self.get_id()
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit))
		if res > 1:
			ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
			print('Exception raise failure') 



class Bot_mention(threading.Thread):
        
	def __init__(self, name,api,uid):
		threading.Thread.__init__(self,name=name) 
		self.api = api
		self.uid = uid
		filehandler = logging.FileHandler(app.config['UPLOAD_PATH']+str(uid)+'/logs.log', 'a')
		log = logging.getLogger()
		for hdlr in log.handlers[:]:
			if isinstance(hdlr,logging.FileHandler): 
				log.removeHandler(hdlr)
		log.addHandler(filehandler)

	def run(self):
		try:
			logging.info("mention thread running")
			while True:
				filename  = app.config['UPLOAD_PATH']+str(self.uid)+'/ls_seen/last_seen.txt'
				mentions = reversed(self.api.mentions_timeline(self.get_last_seen(filename)))
				for mention in mentions:
					last_id = mention.id
					self.store_last_seen(last_id,filename)
					self.api.update_status("@"+str(mention.user.screen_name)+" DM me for more content",mention.id)
					logging.info("Commented to "+str(mention.user.screen_name))
				time.sleep(30)
		finally:
			logging.info("Mention function stopped")


	def store_last_seen(self,last_id,filename):
		with open(filename,'w') as f:
			f.write(str(last_id))
		return

	def get_last_seen(self,filename):
		with open(filename,'r') as f:
			try:
				last_id = int(f.read().strip())
			except:
				last_id = None
		return last_id

	def get_id(self):
		if hasattr(self, '_thread_id'):
			return self._thread_id
		for id, thread in threading._active.items():
			if thread is self:
				return id

	def raise_exception(self):
		thread_id = self.get_id()
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit))
		if res > 1:
			ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
			print('Exception raise failure') 




class Bot_reply(threading.Thread):
        
	def __init__(self, name,api,uid):
		threading.Thread.__init__(self,name=name) 
		self.api = api
		self.uid = uid
		filehandler = logging.FileHandler(app.config['UPLOAD_PATH']+str(uid)+'/logs.log', 'a')
		log = logging.getLogger()
		for hdlr in log.handlers[:]:
			if isinstance(hdlr,logging.FileHandler): 
				log.removeHandler(hdlr)
		log.addHandler(filehandler)

	def run(self):
		try:
			logging.info("reply thread running")
			while True:
				user_set = User_settings.query.filter_by(user_id=self.uid).first()
				time.sleep(int(user_set.DM_reply_time)*60)
				dms = reversed(self.api.list_direct_messages())

				files_img = ['media/'+str(self.uid)+'/img/'+v for v in os.listdir('media/'+str(self.uid)+'/img/')]
				files_vid = ['media/'+str(self.uid)+'/vid/'+v for v in os.listdir('media/'+str(self.uid)+'/vid/')]

				rd_img = random.randint(0,len(files_img)-1)
				rd_vid = random.randint(0,len(files_img)-1)

				qna_sub = json.loads(user_set.questions_sub)
				qna_unsub = json.loads(user_set.questions_unsub)

				msg_path = app.config['UPLOAD_PATH']+str(self.uid)+"/ls_seen/msg_seen.txt"
				prev_msg = self.get_msg(msg_path)		
				
				new_msg = {}
				for dm in dms:
					if dm.message_create['sender_id'] != self.api.me().id_str:
						if dm.message_create['sender_id'] not in prev_msg.keys():
							prev_msg[dm.message_create['sender_id']] = {}
							prev_msg[dm.message_create['sender_id']][dm.created_timestamp] = dm.message_create['message_data']['text']
						else:
							if dm.created_timestamp not in prev_msg[dm.message_create['sender_id']].keys():
								new_msg[dm.message_create['sender_id']] = dm.message_create["message_data"]['text']
								prev_msg[dm.message_create['sender_id']][dm.created_timestamp] = dm.message_create["message_data"]['text']


				for sender_id, msg in new_msg.items():
					if sender_id not in user_set.block_names.split(" "):
						sent = False
						if any([True if v in msg.lower().split(' ') else False for v in ['pic','picture','image','sample']]):
							med = self.api.media_upload(filename  = files_img[rd_img])
							self.api.send_direct_message(sender_id, text="Here's the sample image...",attachment_type='media', attachment_media_id=med.media_id)
							sent = True
						elif any([True if v in msg.lower().split(' ') else False for v in ['vid','video','vidz']]):
							med = self.api.media_upload(filename  = files_vid[rd_vid])
							self.api.send_direct_message(sender_id, text="Here's the sample video...",attachment_type='media', attachment_media_id=med.media_id)
							sent = True
						else:
							if sender_id in user_set.sub_names.split(" "):
								for que,ans in qna_sub.items():
									if td.jaccard(que.strip().lower(),msg.strip().lower()) > 9 or que.strip().lower() == msg.strip().lower():
										self.api.send_direct_message(sender_id,text=ans)
										sent = True
							else:
								for que,ans in qna_unsub.items():
									if td.jaccard(que.strip().lower(),msg.strip().lower()) > 9 or que.strip().lower() == msg.strip().lower():
										self.api.send_direct_message(sender_id,text=ans)
										sent = True
						if not sent:
							self.api.send_direct_message(sender_id,text="Hello! thank you for messaging, Im busy will get back to you after 5 mins.")
						logging.info("Replied to DM :- "+self.api.get_user(sender_id).screen_name)
				self.store_msg(json.dumps(prev_msg),msg_path)
		finally:
			logging.info("Reply function stopped")


	def get_id(self):
		if hasattr(self, '_thread_id'):
			return self._thread_id
		for id, thread in threading._active.items():
			if thread is self:
				return id




	def store_msg(self,json_str,filename):
		with open(filename,'w') as f:
			f.write(json_str)
		return

	def get_msg(self,filename):
		with open(filename,'r') as f:
			try:
				last_id = json.loads(f.read())
			except:
				last_id = {}
		return last_id


	def raise_exception(self):
		thread_id = self.get_id()
		res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit))
		if res > 1:
			ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
			print('Exception raise failure')