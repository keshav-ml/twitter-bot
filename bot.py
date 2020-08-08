import tweepy
import time
import random
import json
import threading
from __init__ import db, User_settings, twitter_bot, User
import logging
import os
import ctypes

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

class Bot(threading.Thread):
        
	def __init__(self, name,api,uid,user_set):
		threading.Thread.__init__(self,name=name) 
		self.api = api
		self.uid = uid
		self.user_set = user_set
		
	def run(self):
		try:
			while True:
				reply = threading.Thread(target=self.bot_reply)
				reply.start()
				mention = threading.Thread(target=self.bot_mention)
				mention.start()
				tweet = threading.Thread(target=self.bot_tweet)
				tweet.start()
				time.sleep(15)
				if mention.is_alive():
					mention.join()
				if reply.is_alive():
					reply.join()
		finally:
			logging.info("sub threads stopped")

		
	def bot_reply(self):
		mentions = self.api.list_direct_messages()
		files = ['media/'+str(self.uid)+'/'+v for v in os.listdir('media/'+str(self.uid)+'/')]
		rand_file = random.randint(0,len(files)-1)
		message = {}
		for mention in mentions:
			if mention.message_create['sender_id'] not in message:
				message[mention.message_create['sender_id']] = mention.message_create["message_data"]['text']
		for sender_id, msg in message.items():
			if any([True if v in msg.lower().split(' ') else False for v in ['pic','picture','image','sample']]):
				med = self.api.media_upload(filename  = files[rand_file])
				self.api.send_direct_message(sender_id, text="Here's the sample image...",attachment_type='media', attachment_media_id=med.media_id)
			else:
				self.api.send_direct_message(sender_id,text=twitter_bot.get_response(msg).text)
		time.sleep(10)

	def bot_mention(self):
		pass

	def bot_tweet(self):
		logging.info("tweet thread running")		
		tweets = json.loads(self.user_set.tweets)
		rand_int = random.randint(0,len(tweets)-1)
		files = ['media/'+str(self.uid)+'/'+v for v in os.listdir('media/'+str(self.uid)+'/')]
		rand_file = random.randint(0,len(files)-1)
		if random.randint(0,10) % 2 == 0:
			med = self.api.media_upload(filename  = files[rand_file])
			#self.api.update_status(tweets[rand_int],media_ids=[med.media_id])
			logging.info("tweeted with media")
		else:
			#self.api.update_status(tweets[rand_int])
			logging.info("tweeted without media")
		time.sleep(self.user_set.tweet_time)
		logging.info("tweet thread destroyed")

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
		