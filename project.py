from flask import Flask, render_template, request, url_for, redirect

from datetime import datetime
from flask.ext.pymongo import PyMongo
from pymongo import MongoClient
import validators
from bson.objectid import ObjectId

app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme

@app.route('/vote/<m_id>')
def upvote(m_id):
	db.links.update({'_id': ObjectId(m_id)}, 
					{'$inc': {'votes': int(1)}})
	return redirect(url_for('display'))

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
				'votes': 1,
				'_id':1
				})

			return render_template('form.html', alert="ok")

	return render_template('form.html')
@app.route('/all')
def display():
	return render_template("info.html", data = db.links.find().sort('upvote').sort('current_time'))

if __name__ == '__main__': # if it was called by python interpreter, no imported to another .py file
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
