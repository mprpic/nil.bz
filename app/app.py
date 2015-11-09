import sys
import config
from flask import Flask, render_template

DEBUG = 'DEBUG' in environ.keys()

app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("soon.html")
    # return render_template("about.html")

@app.route('/blog')
def blog():
    return render_template("soon.html")
    # return render_template("blog.html")

@app.route('/climbing-log')
def climbing():
    return render_template("soon.html")
    # remove function: static

@app.route('/ferrata-log')
def ferrata():
    return render_template("soon.html")
    # remove function: static

@app.route('/photos')
def photos():
    return render_template("photos.html")

@app.route('/projects')
def projects():
    return render_template("soon.html")
    # return render_template("projects.html")

if __name__ == '__main__':
    app.run(debug=DEBUG)
