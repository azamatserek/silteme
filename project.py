from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash
from flask.ext.bcrypt import Bcrypt as bcrypt

from datetime import datetime
from flask.ext.pymongo import PyMongo
from pymongo import MongoClient
import validators
from bson.objectid import ObjectId

app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme

@app.route('/vote/<m_id>', methods=['GET'])
def upvote(m_id):
	if request.method == 'GET':
		print "get request"
		db.links.update({'_id': ObjectId(m_id)}, 
						{'$inc': {'votes': int(1)}})
		# return redirect(url_for('display'))
		return "hello"

@app.route('/', methods=['GET', 'POST'])
def index():
	session['username'] = 'Abzal'
	if request.method == "POST":
		if 'username' in session:
			url = request.form["url"]
			links = db.links
			if not validators.url(url):
				url = "http://" + url
			if not validators.url(url):
			    return "INCORRECT URL"
			else:
				existing_url = links.find_one({'url': url})
				if not existing_url:
					author = request.form["author"]
					current_time = str(datetime.now())

					print current_time
					print url
					print author
					
					db.links.insert({
						'url': url, 
						'author': author, 
						'current_time': current_time,
						'votes': 1
						})

					return render_template('form.html', alert="ok")
				else:
					return render_template('form.html',alert2 = "ok")
		else:
			redirect(url_for('login'))

	return render_template('form.html')

@app.route('/all')
def display():
	return render_template("info.html", data = db.links.find().sort('upvote').sort('current_time'))


@app.route('/login', methods = ['POST'])
def login():
	users = mongo.db.users
	login_user = users.find_one({'name':request.form['username']})
	if login_user:
		if bcrypt.hashpw(request.form['pass'].encode('utf-8'),login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
			session['username'] = request.form['username']
			return redirect(url_for('index'))
	return 'Invalid username/password combination'

@app.route('/register', methods = ['POST', 'GET'])
def register():
	if request.method == 'POST':
		users = mongo.db.users
		existing_user = users.find_one({'name': request.form['username']})
		if existing_user is None:
			hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'),bcrypt.getsalt())
			users.insert({'name':request.form['username'], 'password': hashpass})
			session['username'] = request.form['username']
			return redirect(url_for('index'))
		return 'That username already exists'
	return render_template('register.html')
	

if __name__ == '__main__':
	app.secret_key = 'fha87vyfsd87vyfd87vydsf87vydfs8v7ydfsv87dfsyv87dfyv87dsfyv'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
