import os
import cv2
import cv2.cv as cv

rootdir = '/Users/tim/mycode/findeyes/data/allarticles'
CROP_DIR = '../images/faces'
FACE_CLASSIFIER = '/usr/local/Cellar/opencv/2.4.11_1/share/OpenCV/haarcascades/haarcascade_frontalface_default.xml'

face_cl = cv2.CascadeClassifier(FACE_CLASSIFIER)
crop_file = '{}/{}-{}.jpg'
for root, dirs, files in os.walk(rootdir, topdown=True):
	for file in files:
		if file[-3:] == 'jpg':
			f = 1
			print 'Processing {}'.format(file) 
			try:
				image = cv2.imread(os.path.join(root, file), 0)
				faces = face_cl.detectMultiScale(image, scaleFactor=1.3, minNeighbors=3, minSize=(100, 100), flags=cv.CV_HAAR_SCALE_IMAGE)
			except cv2.error:
				pass
			else:
				for (x,y,w,h) in faces:
					face = image[y:y+h, x:x+w]
					cv2.imwrite(crop_file.format(CROP_DIR, os.path.basename(file), f), face)
	    			f += 1