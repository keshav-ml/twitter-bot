import tweepy
import time

def bot_reply():
	pass

def bot_mention():
	pass

def bot_tweet(api,message,filename=None):
	if filename:
		api.send_direct_message(message,filename  = filename)
	else:
		api.update_status(message)

def bot(api,user_obj,user_settings):
	while True:
		bot_reply()
		bot_tweet()
		bot_mention()

	