#!/usr/bin/env python3
#twitterbot
# Imports
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import requests

client_key = "wa5j9nCdlKlJX4fJx0j68nrZP"
client_secret = "sc858349LPKbQcatgKQIddGo6NDHNrwupiUxWvmadiI6SjddGB"
token = "1185295810155683845-fzcH7NUOLS8ehyiuFkFCwdyLsDUkXV"
token_secret = "inVaDGycX7wkTGmhNvAiRqL7m56YdPgk1W5IgGbzhNFxa"

def notify_discord(text):
	url = "https://discordapp.com/api/webhooks/656646611652444183/ISoGKFvV1fpSTxbJbSmhGD03FAGj3F866NrkKhErzfhLFJ9fCw6GyNfCq7N9U99EsWJ4"
	payload = {"username": "SHiFT Codes", "content": text}

	r = requests.post(url, json=payload)

	print(r.text)

class TweetListener(StreamListener):

	def on_data(self, data):
		tweets = json.loads(data)
		if str(tweets['in_reply_to_status_id_str']) == 'None' and 'retweeted_status' not in tweets str(tweets['name']) == 'SHiFT Codes':
			notify_discord(tweets['text'])

		return True

	def on_error(self, status):
		print(f'Error: {status}')


listener = TweetListener()
auth = OAuthHandler(client_key, client_secret)
auth.set_access_token(token, token_secret)

stream = Stream(auth, listener)
stream.filter(follow=['906234810'])
