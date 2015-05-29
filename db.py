import time
import os
import re
from datetime import datetime
import requests
import calendar
import random
from pymongo import MongoClient, GEO2D
from PIL import Image

from credentials import TROVE_API_KEY, MONGOLAB_URL

rootdir = '../images/faces'

def populate_db():
    '''
    Populates a Mongo database with metadata from the filenames
    of the faces and eyes located py rootdir.
    '''
    for root, dirs, files in os.walk(rootdir, topdown=True):
        dbclient = MongoClient(MONGOLAB_URL)
        db = dbclient.get_default_database()
        faces = db.fd_faces
        faces.ensure_index([('random_id', GEO2D)])
        titles = {}
        for f in files:
            im = Image.open(os.path.join(root, file), 0)
            f_name, ext = os.path.splitext(f)
            if ext == '.jpg':
                print 'Processing {}'.format(f_name)
                details = f_name.split('-')
                date_str = details[0]
                title_id = details[1]
                article_id = details[2]
                face_id = details[3]
                #face['eyes'] = face['eyes'].append(eye_id)
                date_obj = datetime(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
                if title_id in titles:
                    title = titles[title_id]
                else:
                    r = requests.get('http://api.trove.nla.gov.au/newspaper/title/{}?encoding=json&key={}'.format(title_id, TROVE_API_KEY))
                    results = r.json()
                    title = results['newspaper']['title']
                    title = re.search(r'(.*)\(.*\)', title).group(1).strip()
                    titles[title_id] = title
                    time.sleep(.5)
                face = {}
                face['_id'] = '{}-{}'.format(article_id, face_id)
                face['image'] = f_name
                face['width'] = im.size[0]
                face['height'] = im.size[1]
                face['date'] = date_obj
                face['article_id'] = article_id
                face['title'] = title
                face['title_id'] = title_id
                face['face_id'] = face_id
                face['random_id'] = [random.random(), 0]
                faces.save(face)

