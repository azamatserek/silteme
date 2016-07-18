import threading

import pymongo
from pymongo import MongoClient
import time


client = MongoClient()
db = client.silteme
T_update = 5 * 60 # seconds
MAX_LINKS_SIZE = 500

# this function returns a rating value for the given number of votes and live time in seconds
def get_rating (votes, life_time):
	life_time_hours = life_time / 60.0 / 60.0 # converting seconds to hours
	gravity = 1.8
	return votes / (life_time_hours + 2) ** gravity

def set_interval(func, sec):
	def func_wrapper():
		set_interval(func, sec)
		func()
	t = threading.Timer(sec, func_wrapper)
	t.start()
	return t

def update():
	links = db.links.find({})
	if links.count() > MAX_LINKS_SIZE:
		ids = []
		to_remove = db.links.find({}).sort('add_time').limit(links.count() - MAX_LINKS_SIZE)
		for el in to_remove:
			ids.append(el['_id'])
		for cur_id in ids:
			db.links.remove({'_id': cur_id})
	
	now = time.time()
	for link in links:
		dt = now - link['add_time']
		rating = get_rating(link['votes'], dt)
		db.links.update({
				'_id': link['_id']
			}, {
				'$set': {
					'rating': rating
				}
			})


set_interval(update, T_update)