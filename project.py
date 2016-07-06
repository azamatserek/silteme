from flask import Flask, render_template, request

app = Flask(__name__) 

@app.route('/', methods=['GET', 'POST'])
def HelloWorld():
	if request.method == "POST":
		url = request.form["url"]
		print url
	return render_template('form.html', user="Azamat")

if __name__ == '__main__': # if it was called by python interpreter, no imported to another .py file
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
