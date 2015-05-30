from PIL import Image, ImageOps, ImageDraw, ImageFilter
import os
import cv2
import cv2.cv as cv
import credentials
import tweepy
import requests
import redis
from StringIO import StringIO
import random
import time
from pymongo import MongoClient, GEO2D
try:
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass

from credentials import MONGOLAB_URL



FACE_CLASSIFIER = '/usr/local/Cellar/opencv/2.4.11_1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml'
FACE_CLASSIFIER = '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml'

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

auth = tweepy.OAuthHandler(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET)
auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)

def mask(im):
	'''Add a nice elliptical mask to images.'''
	#You get a nicer result if you start big and then resize.
	old_width = im.size[0] * 3
	old_height = im.size[1] * 3
	new_width = int(old_width * .7)
	new_height = int(old_height * .95)
	bigsize = (old_width, old_height)
	x_offset = (old_width - new_width) / 2
	y_offset = (old_height - new_height) / 2
	ellipse_size = (x_offset , y_offset, new_width + x_offset, new_height + y_offset)
	mask = Image.new('L', bigsize, 0)
	draw = ImageDraw.Draw(mask) 
	draw.ellipse(ellipse_size, fill=160)
	mask = mask.resize(im.size, Image.ANTIALIAS)
	#Blur radius is small so apply multiple times for extra fuzziness.
	n = 0
  	while n < 3:
		mask = mask.filter(ImageFilter.BLUR)
		n += 1
	#output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
	output = im.copy()
	output.putalpha(mask)
	return output


def add_faces(tweet_image, output_path='output.jpg', max_faces=4):
	'''Replace faces in photos with faces from the Face Depot.'''
	dbclient = MongoClient(MONGOLAB_URL)
	db = dbclient.get_default_database()
	fd_faces = db.fd_faces
	tweet_image.save('temp.jpg')
	cv_image = cv2.imread('temp.jpg', 0)
	os.remove('temp.jpg')
	face_cl = cv2.CascadeClassifier(FACE_CLASSIFIER)
	faces = face_cl.detectMultiScale(cv_image, scaleFactor=1.2, minNeighbors=3, minSize=(100, 100), flags=cv.CV_HAAR_SCALE_IMAGE)
	articles = []
	for f_index, (x,y,w,h) in enumerate(faces[:max_faces]):
		new_faces = list(fd_faces.find({'random_id': {'$near': [random.random(), 0]}}).limit(1))
		new_face_url = 'http://facedepot.s3.amazonaws.com/{}.jpg'.format(new_faces[0]['image'])
		article_id = new_faces[0]['article_id']
		article_url = 'http://nla.gov.au/nla.news-article{}'.format(article_id)
		articles.append(article_url)
		response = requests.get(new_face_url, stream=True)
		new_face = Image.open(StringIO(response.content)).convert('RGBA')
		#new_face = Image.open('../images/faces/{}.jpg'.format(new_faces[0]['image'])).convert('RGBA')
		new_face = new_face.resize((w,h), Image.ANTIALIAS)
		new_face = mask(new_face)
		tweet_image.paste(new_face, (x, y), new_face)
	tweet_image.save(output_path)
	return [output_path, articles]


def process_tweet(tweet):
	tweet_id, tweet_author, image_url = tweet.split(' | ')
	response = requests.get(image_url, stream=True)
	tweet_image = Image.open(StringIO(response.content))
	faces_added = add_faces(tweet_image, output_path='output-{}.jpg'.format(tweet_id))
	if faces_added[1]:
		text = '{} See: {}'.format(tweet_author, ', '.join(faces_added[1]))
	else:
		text = '{} Sorry, we were unable to fit your face. Please try an alternative photograph.'.format(tweet_author)
	status = api.update_with_media(filename=faces_added[0], status=text, in_reply_to_status_id=tweet_id)
	#status = text
	os.remove('output-{}.jpg'.format(tweet_id))
	time.sleep(20)
	return status.text
		

	

