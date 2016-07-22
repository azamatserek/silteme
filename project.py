from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash
from flask.ext.bcrypt import Bcrypt

from flask_paginate import Pagination

from bs4 import BeautifulSoup as bf
import urllib2

from datetime import datetime
from flask.ext.pymongo import PyMongo
from pymongo import MongoClient
import validators
from bson.objectid import ObjectId
import time
import os


from updater import get_rating


app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme
bcrypt = Bcrypt(app)

def render (template='info.html', **kw):
	search = False
	q = request.args.get('q')
	if q:
		search = True
	page = request.args.get('page', type=int, default=1)
	links = db.links.find().sort('rating', -1).limit(page * 10).skip((page - 1) * 10)
	pagination = Pagination(page=page, total=links.count(), search=search, record_name='links')
	return render_template(template, links=links, pagination=pagination, user=session.get('username'), **kw)

@app.route('/vote/<m_id>', methods=['GET'])
def upvote(m_id):
	if request.method == 'GET':
		username = session.get('username')
		# print username
		if username is None:
			flash('You are not logged in')
			return redirect(url_for('login'))
		else:
			l_id = m_id
			u_id = db.users.find_one({'name': username})['_id']
			exists = db.user_votes.find_one({'u_id': u_id, 'l_id': l_id})
			if exists:
				pass
			else:
				db.links.update({'_id': ObjectId(m_id)}, 
							{'$inc': {'votes': int(1)}})
				db.user_votes.insert({'u_id': u_id,'l_id': l_id})
		return "hello"

@app.route('/', methods = ['GET', 'POST'])
def display():
	if request.method == 'GET':
		return render()
	if request.method == 'POST':
		if 'username' in session:
			url = request.form["url"]
			if not validators.url(url):
				url = "http://" + url
			if not validators.url(url):
			    return render(error_url='URL is incorrect (validator failed)')
			else:
				existing_url = db.links.find_one({'url': url})
				if not existing_url:
					current_time = time.time()
					cur_user = db.users.find_one({'name': session['username']})
					html = None
					try:
						html = urllib2.urlopen(url)
						html = html.read()
						soup = bf(html)
						title = url
						try:
							title = soup.find('title').text
						except Exception:
							pass
						
						link_id = db.links.insert({
							'url': url, 
							'title': title,
							'author': cur_user['name'],
							'author_id': cur_user['_id'],
							'add_time': current_time,
							'votes': 1,
							'rating': get_rating(1, 0)
							})

						db.user_votes.insert({'u_id': cur_user['_id'],'l_id': ObjectId(link_id)})
						return render(error_url="New item is added")
					except Exception:
						return render(error_url="URL is incorrect")
				else:
					return render(error_url="URL already exists")
		else:
			flash('Please log in')
			return redirect(url_for('login'))


@app.route('/login', methods = ['GET', 'POST'])
def login():
	print request.form
	if request.method == 'POST':
		users = db.users
		login_user = users.find_one({'name':request.form['username']})
		if login_user:
			if bcrypt.check_password_hash(login_user['password'], request.form['pass'].encode('utf-8')):
				session['username'] = request.form['username']
				flash('successfully logged in')
				return redirect(url_for('display'))
		error = 'Invalid username/password combination'
		return render(data=request.form, error=error)

	return render()

@app.route('/register', methods = ['POST', 'GET'])
def register():
	if request.method == 'POST':
		users = db.users
		existing_user = users.find_one({'name': request.form['username']})
		if existing_user is None:
			hashpass = bcrypt.generate_password_hash(request.form['pass'].encode('utf-8'))
			users.insert({'name':request.form['username'], 'password': hashpass})
			session['username'] = request.form['username']
			flash('successfully registered')
			return redirect(url_for('display'))
		error = 'That username already exists'
		return render(data=request.form, error=error)
	return render()

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('display'))


@app.template_filter('ctime')
def timectime(s):
	return time.ctime(s) # datetime.datetime.fromtimestamp(s)

if __name__ == '__main__':
	app.secret_key = 'fha87vyfsd87vyfd87vydsf87vydfs8v7ydfsv87dfsyv87dfyv87dsfyv'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
