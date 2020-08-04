import tweepy
import time
import random
import json
import threading
import logging
import os

format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

class Bot():
	def __init__(self, api,user,user_set):
		self.api = api
		self.user = user
		self.user_set = user_set
		
		
	def bot_reply(self,stop_eve):
		pass

	def bot_mention(self,stop_eve):
		pass

	def bot_tweet(self,stop_eve):
		logging.info("tweet thread running")		
		tweets = json.loads(self.user_set.tweets)
		rand_int = random.randint(0,len(tweets)-1)
		files = ['media/'+str(self.user.id)+'/'+v for v in os.listdir('media/'+str(self.user.id)+'/')]
		rand_file = random.randint(0,len(files)-1)
		while not stop_eve.is_set():
			if random.randint(0,10) % 2 == 0:
				med = self.api.media_upload(filename  = files[rand_file])
				self.api.update_status(tweets[rand_int],media_ids=[med.media_id])
				logging.info("tweeted with media")
			else:
				self.api.update_status(tweets[rand_int])
				logging.info("tweeted without media")
			time.sleep(int(self.user_set.tweet_time))

	def bot_start(self,stop_eve):
		stop_event = threading.Event()
		logging.info("creating sub threads")
		reply_th = threading.Thread(name = "reply_thread",target=self.bot_reply, args=(stop_event,))
		reply_th.setDaemon(True)
		mention_th = threading.Thread(name='mention_thread',target=self.bot_mention, args=(stop_event,))
		mention_th.setDaemon(True)
		tweet_th = threading.Thread(name='tweet_thread',target=self.bot_tweet, args=(stop_event,))
		tweet_th.setDaemon(True)
		tweet_th.start()
		reply_th.start()
		mention_th.start()
		if stop_eve.is_set():
			stop_event.set()
			logging.info("Sub threads  destroyed")