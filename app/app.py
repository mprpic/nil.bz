import sys
import config
from flask import Flask, render_template
from os import environ

DEBUG = 'DEBUG' in environ.keys()

app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def home():
    return render_template("home.html")

@app.route('/about', strict_slashes=False)
def about():
    return render_template("soon.html")
    # return render_template("about.html")

@app.route('/blog', strict_slashes=False)
def blog():
    return render_template("soon.html")
    # return render_template("blog.html")

@app.route('/climbing-log', strict_slashes=False)
def climbing():
    return render_template("soon.html")
    # remove function: static

@app.route('/ferrata-log', strict_slashes=False)
def ferrata():
    return render_template("soon.html")
    # remove function: static

@app.route('/photos', strict_slashes=False)
def photos():
    return render_template("photos.html")

@app.route('/projects', strict_slashes=False)
def projects():
    return render_template("soon.html")
    # return render_template("projects.html")

if __name__ == '__main__':
    app.run(debug=DEBUG)
