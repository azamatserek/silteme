from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash
from flask.ext.bcrypt import Bcrypt


from bs4 import BeautifulSoup as bf
import urllib2


from datetime import datetime
from flask.ext.pymongo import PyMongo
from pymongo import MongoClient
import validators
from bson.objectid import ObjectId

app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme
bcrypt = Bcrypt(app)

def render (template, **kw):
	return render_template(template, user=session.get('username'), **kw)

# this function returns a rating value for the given number of votes and live time in seconds
def getRating (votes, live_time):
	live_time_hours = live_time / 60.0 / 60.0 # converting seconds to hours
	gravity = 1.8
	return votes / (live_time_hours + 2) ** gravity

@app.route('/vote/<m_id>', methods=['GET'])
def upvote(m_id):
	if request.method == 'GET':
		username = session.get('username')
		print username
		if username is None:
			flash('You are not logged in')
			return redirect(url_for('login'))
		else:
			l_id = m_id
			u_id = db.users.find_one({'name': username})['_id']
			exists = db.user_votes.find_one({'u_id': u_id, 'l_id': l_id})
			if exists:
				print exists
			else:
				db.links.update({'_id': ObjectId(m_id)}, 
							{'$inc': {'votes': int(1)}})
				db.user_votes.insert({'u_id': u_id,'l_id': l_id})
	
		return "hello"

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == "POST":
		if 'username' in session:
			url = request.form["url"]
			links = db.links
			if not validators.url(url):
				url = "http://" + url
			if not validators.url(url):
			    return render('form.html', error='URL is incorrect')
			else:
				existing_url = links.find_one({'url': url})
				if not existing_url:
					current_time = str(datetime.now())

					print current_time
					print url

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
						
						db.links.insert({
							'url': url, 
							'title': title,
							'author': cur_user['name'],
							'author_id': cur_user['_id'],
							'current_time': current_time,
							'votes': 1
							})

						return render('form.html', error="New item is added")

					except Exception:
						return render('form.html', error="URL is incorrect")

				else:
					return render('form.html', error="URL already exists")
		else:
			flash('Please log in')
			redirect(url_for('login'))

	return render('form.html')

@app.route('/all')
def display():
	return render("info.html", data = db.links.find().sort('upvote').sort('current_time'))


@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		users = db.users
		login_user = users.find_one({'name':request.form['username']})
		if login_user:
			if bcrypt.check_password_hash(login_user['password'], request.form['pass'].encode('utf-8')):
				session['username'] = request.form['username']

				flash('successfully logged in')
				return redirect(url_for('index'))
		error = 'Invalid username/password combination'
		return render('login.html', data=request.form, error=error)

	return render('login.html')

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
			return redirect(url_for('index'))
		error = 'That username already exists'
		return render('register.html', data=request.form, error=error)
	return render('register.html')
	

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('index'))


if __name__ == '__main__':
	app.secret_key = 'fha87vyfsd87vyfd87vydsf87vydfs8v7ydfsv87dfsyv87dfyv87dsfyv'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
