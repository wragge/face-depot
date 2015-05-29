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
from pymongo import MongoClient, GEO2D

from credentials import MONGOLAB_URL

def mask(im):
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
	n = 0
  	while n < 3:
		mask = mask.filter(ImageFilter.BLUR)
		n += 1
	#output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
	output = im.copy()
	output.putalpha(mask)
	return output

FACE_CLASSIFIER = '/usr/local/Cellar/opencv/2.4.11_1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml'

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

auth = tweepy.OAuthHandler(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET)
auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)

dbclient = MongoClient(MONGOLAB_URL)
db = dbclient.get_default_database()
fd_faces = db.fd_faces

mentions = api.mentions_timeline()
for t_index, tweet in enumerate(mentions):
	try:
		image_url = tweet.entities['media'][0]['media_url']
	except (KeyError, IndexError):
		print 'No image'
	else:
		response = requests.get(image_url, stream=True)
		image = Image.open(StringIO(response.content))
		image.save('temp.jpg')
		img = cv2.imread('temp.jpg', 0)
		face_cl = cv2.CascadeClassifier(FACE_CLASSIFIER)
		faces = face_cl.detectMultiScale(img, scaleFactor=1.1, minNeighbors=2, minSize=(100, 100), flags=cv.CV_HAAR_SCALE_IMAGE)
		for f_index, (x,y,w,h) in enumerate(faces):
			new_faces = list(fd_faces.find({'random_id': {'$near': [random.random(), 0]}}).limit(1))
			face =Image.open('{}/{}.jpg'.format('/Users/tim/mycode/facedepot/images/faces', new_faces[0]['image'])).convert('RGBA')
			#face.show()
			#face = ImageOps.autocontrast(face, 5).convert('RGBA')
			new_mask = mask(face)
			new_mask.show()
			new_face = new_mask.resize((w,h), Image.ANTIALIAS)
			image.paste(new_face, (x, y), new_face)
		image.save('output-{}.jpg'.format(t_index))
		

	

