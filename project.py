from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash

from datetime import datetime
from flask.ext.pymongo import PyMongo
from pymongo import MongoClient
import validators
from bson.objectid import ObjectId
from flask_oauth import OAuth

app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme

oauth = OAuth()
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='KAQ45VO0Dmr7FtjSMYyHCQZIm',
    consumer_secret='kyQig4g3rGNviDZMBMO0cWhf4k7Esb0rCgMXlYBbU0AVEqNBBm'
)

@app.route('/vote/<m_id>', methods=['GET'])
def upvote(m_id):
	if request.method == 'GET':
		print "get request"
		db.links.update({'_id': ObjectId(m_id)}, 
						{'$inc': {'votes': int(1)}})
		# return redirect(url_for('display'))
		return "hello"

@app.route('/', methods=['GET', 'POST'])
def HelloWorld():
	if request.method == "POST":
		url = request.form["url"]

		if not validators.url(url):
			url = "http://" + url

		if not validators.url(url):
		    return "INCORRECT URL"
		else:
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

	return render_template('form.html')

@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

@app.route('/login')
def login():
	return twitter.authorize(callback=url_for('oauth_authorized',
		next=request.args.get('next') or request.referrer or url_for('HelloWorld')))

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
	next_url = request.args.get('next') or url_for('HelloWorld')
	if resp is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)

	session['twitter_token'] = (
		resp['oauth_token'],
		resp['oauth_token_secret']
	)
	session['twitter_user'] = resp['screen_name']

	flash('You were signed in as %s' % resp['screen_name'])
	return redirect(next_url)


@app.route('/all')
def display():
	return render_template("info.html", data = db.links.find().sort('upvote').sort('current_time'))


if __name__ == '__main__': # if it was called by python interpreter, no imported to another .py file
	app.secret_key = 'super secret key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)
