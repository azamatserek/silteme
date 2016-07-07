from flask import Flask, render_template, request
from datetime import datetime

import validators

app = Flask(__name__) 


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

			data = {
				"url": url,
				"author": author,
				"time": current_time
			}

			return render_template("info.html", data=data)


	return render_template('form.html')

if __name__ == '__main__': # if it was called by python interpreter, no imported to another .py file
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
