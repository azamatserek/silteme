#coding=utf8

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from flask import session
from flask import flash
from flask.ext.bcrypt import Bcrypt
from flask.ext.pymongo import PyMongo
from flask.ext.mail import Mail, Message
from flask_paginate import Pagination

from bs4 import BeautifulSoup as bf
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId

from updater import get_rating

import urllib2
import time
import validators
import os
import hashlib

app = Flask(__name__) 
mongo = PyMongo(app)
connection = MongoClient()
db = connection.silteme
bcrypt = Bcrypt(app)
mail = Mail(app)

app.config.update(
	SECRET_KEY = 'fha87vyfsd87vyfd87vydsf87vydfs8v7ydfsv87dfsyv87dfyv87dsfyv',
	DEBUG = True,
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = 587,
	MAIL_USE_TLS = True,
	MAIL_USE_SSL = False,
	MAIL_USERNAME = 'silteme.kz@gmail.com',
	MAIL_PASSWORD = 'silteme123',
	DEFAULT_MAIL_SENDER = 'silteme.kz@gmail.com')


def render (template='info.html', **kw):
	search = False
	q = request.args.get('q')
	if q:
		search = True
	page = request.args.get('page', type=int, default=1)
	links = db.links.find().sort('rating', -1).limit(10).skip((page-1)*10)
	# display_msg = '[' + str((page-1)*10+1) + '...' + str(min(page*10, links.count())) + u'] из ' + str(db.links.find().count())
	pagination = Pagination(display_msg=' ', page=page,  css_framework='foundation', total=links.count(), search=search, record_name='links')
	return render_template(template, links=links, pagination=pagination, user=session.get('username'), **kw)

@app.route('/vote/<m_id>', methods=['GET'])
def upvote(m_id):
	if request.method == 'GET':
		username = session.get('username')
		if username is None:
			return 'error, Вы не вошли в систему'
		else:
			l_id = m_id
			u_id = db.users.find_one({'name': username})['_id']
			exists = db.user_votes.find_one({'u_id': u_id, 'l_id': l_id})
			if exists:
				return u"error, Вы уже голосовали"
			else:
				db.links.update({'_id': ObjectId(m_id)}, 
							{'$inc': {'votes': int(1)}})
				db.user_votes.insert({'u_id': u_id,'l_id': l_id})
		return u"success, Ваш голос принят"

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
				flash(u'Неправильный URL', 'error')
				return render()
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
						flash(u"Добавлена новая ссылка", 'success')
						return render()
					except Exception:
						flash(u'Неправильный URL', 'error')
						return render()
				else:
					flash(u'Такой URL уже существует', 'warning')
					return render()
		else:
			flash(u'Пожалуйста, войдите в систему', 'warning')
			return redirect(url_for('login'))

@app.route('/restore/<token>', methods=['GET', 'POST'])
def restore(token):
	if request.method == 'GET':
		return render(restore=True)
	elif request.method == 'POST':
		forgot = db.forgot.find_one({'token': token})
		if forgot:
			email = forgot['email']
			user = db.users.find_one({'email': email})
			password = request.form['pass']
			if len(password) < 6:
				return render(restore=True, error=u'Длина пароля должна состоять как минимум из 6 символов')
			hashpass = bcrypt.generate_password_hash(password.encode('utf-8'))
			db.users.update({'email': email}, {'$set': {'password': hashpass}})
			db.forgot.remove({'_id': forgot['_id']})
			session['username'] = user['name']
			flash(u'Ваш пароль успешно восстановлен', 'success')
			return render()
		else:
			return render(error=u'Неправильная ссылка')
@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
	if request.method == 'POST':
		users = db.users
		email = request.form['email']
		user = users.find_one({'email': email})
		if user:
			name, password, email = user['name'], user['password'], user['email']
			token = hashlib.sha256(bcrypt.generate_password_hash(password + name + email)).hexdigest()
			
			already = db.forgot.find_one({'email': email})
			if already:
				db.forgot.remove({'_id': already['_id']})

			db.forgot.insert({'email': email, 'token': token})
			html = u'Дорогой %s, <br/><br/>Пожалуйста, пройдите по %s чтобы восстановить свой пароль.<br/><br/>С уважением,<br/>Silteme.kz<br/>Азамат Серек' % (name, 'http://localhost:5000/restore/%s'%token)
			msg = Message(subject=u"Восстановление пароля [silteme.kz]",
				html=html,
				sender='silteme.kz@gmail.com',
				recipients=[email])
			mail.send(msg)
			return render(error=u'Проверьте вашу почту')
		else:
			return render(error=u'В базе нет такой почты')
	return render(error='hi')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		users = db.users
		login_user = users.find_one({'name':request.form['username']})
		if login_user:
			if bcrypt.check_password_hash(login_user['password'], request.form['pass'].encode('utf-8')):
				session['username'] = request.form['username']
				flash(u'Вы успешно вошли в систему', 'success')
				return redirect(url_for('display'))
		error = u'Неправильный введен пароль или логин'
		return render(data=request.form, error=error)

	return render()

@app.route('/register', methods = ['POST', 'GET'])
def register():
	if request.method == 'POST':
		users = db.users
		username = request.form['username']
		password = request.form['pass']
		if 'email' not in request.form:
			return render(data=request.form, email=u'Пожалуйста, введите вашу почтовый адрес')
		email = request.form['email']
		error = ''
		existing_user = users.find_one({'name': username})
		if existing_user is None:
			if len(username) < 3:
				error = u'Логин должен быть длины больше или равно 3'
			if len(password) < 6:
				error = u'Пароль должен быть длины больше или равно 6'
			if users.find_one({'email': email}):
				error = u'Такой почтовый адрес уже занят'
			if len(error) > 0:
				return render(data=request.form, error=error)
			hashpass = bcrypt.generate_password_hash(password.encode('utf-8'))
			users.insert({'name': username, 
				'email': email, 
				'password': hashpass})
			session['username'] = username
			flash(u'Вы успешно зарегистрированы', 'success')
			return redirect(url_for('display'))
		error = u'Такой пользователь уже существует'
		return render(data=request.form, error=error)
	return render()

@app.route('/logout')
def logout():
	session.pop('username', None)
	flash(u'Вы успешно вышли из системы', 'success')
	return redirect(url_for('display'))


@app.template_filter('ctime')
def timectime(s):
	now=time.time()
	return str(timedelta(seconds=now-s)).split(".")[0] + u' назад' # datetime.datetime.fromtimestamp(s)

if __name__ == '__main__':
	mail = Mail(app)
	app.run(host = '0.0.0.0', port = 5000)
