import os
import sys
import config
import hmac
import hashlib
import shutil
import git
import subprocess
from flask import Flask, render_template, redirect, url_for, request

DEBUG = 'DEBUG' in os.environ.keys()

app = Flask(__name__)

def verify_hash(request_body, header_value):
    h = hmac.new(config.repo_secret, request_body, hashlib.sha1)
    return hmac.compare_digest(bytes("sha1=" + h.hexdigest()),
                               bytes(header_value))

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

@app.route('/photos', strict_slashes=False)
def photos():
    return render_template("photos.html")

@app.route('/projects', strict_slashes=False)
def projects():
    return render_template("soon.html")
    # return render_template("projects.html")

@app.route('/regenerate-climbing-logs', methods=['POST'])
def regen_logs():

    header_value = request.headers.get('X-Hub-Signature')
    request_body = request.get_data()

    if verify_hash(request_body, header_value):
        repo = git.cmd.Git(config.climbing_repo)
        repo.pull()

        subprocess.call(["python",
             config.climbing_repo + "generate-log.py",
             "--input", config.climbing_repo + "data/climbing-data.txt",
             "--output", config.web_dir + "climbing/climbing.html",
             "--title", "nil.bz | Climbing Log"])
        subprocess.call(["python",
             config.climbing_repo + "generate-log.py",
             "--ferrata",
             "--input", config.climbing_repo + "data/ferrata-data.txt",
             "--output", config.web_dir + "climbing/ferrata.html",
             "--title", "nil.bz | Ferrata Log"])

        shutil.copy(config.climbing_repo + "css/log.css", config.web_dir + "climbing/")

    return redirect(url_for('home'), code=302)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=DEBUG)
