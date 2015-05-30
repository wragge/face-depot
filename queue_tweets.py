import credentials
import tweepy
import redis
from rq import Queue
import re
from transplant import process_tweet

auth = tweepy.OAuthHandler(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET)
auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
tweet_queue = Queue(connection=redis.Redis())

since_id = redis_client.get('fd_last_tweet_id')
#since_id = None
if since_id:
	mentions = api.mentions_timeline(since_id=since_id, include_rts=False)
else:
	mentions = api.mentions_timeline(include_rts=False)
for t_index, tweet in enumerate(mentions[::-1]):
	if tweet.text[:10] == '@facedepot':
		try:
			image_url = tweet.entities['media'][0]['media_url']
		except (KeyError, IndexError):
			print 'No image'
		else:
			tweet_id = tweet.id
			tweet_author = '@' + tweet.author.screen_name
		tweet_details = '{} | {} | {}'.format(tweet_id, tweet_author, image_url)
		print tweet_details
		result = tweet_queue.enqueue(process_tweet, tweet_details)
	redis_client.set('fd_last_tweet_id', tweet_id)

