import os
import config
import hmac
import hashlib
import shutil
import git
import subprocess
import markdown
from datetime import datetime
from flask import Flask, Markup, render_template, redirect, url_for, request

DEBUG = 'DEBUG' in os.environ.keys()
APP_DIR = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)


@app.route('/')
@app.route('/index.html')
def home():
    return render_template('home.html')


@app.route('/about', strict_slashes=False)
def about():
    return render_template('about.html')


def blog_post_url(post):
    return post.rstrip('.md').split('_')[1]


@app.route('/blog/<post>', strict_slashes=False)
def blog_posts(post):
    # Return posts that start with a date; those that don't are drafts
    posts = [f for f in os.listdir(APP_DIR + '/blog_posts') if f[0:7].isdigit()]
    # Convert post file names into URL IDs
    post_urls = [blog_post_url(p) for p in posts]

    if post in post_urls:
        p = posts[post_urls.index(post)]

        post_date = datetime.strptime(p.split('_')[0], '%Y%m%d') \
                            .strftime('%A, %B %d, %Y')

        with open(APP_DIR + '/blog_posts/' + p) as f:
            content = f.readlines()

        post_title = content[0].replace('Title:', '').strip()
        site_title = 'Blog - ' + post_title

        content = ''.join(content[2:])
        content = Markup(markdown.markdown(content))
        return render_template('blog_template.html', content=content,
                               site_title=site_title, post_title=post_title,
                               post_date=post_date)
    else:
        return render_template('404.html'), 404


@app.route('/blog', strict_slashes=False)
def blog():
    # We can sort (newest first) alphabetically since we're using YYYYMMDD
    posts = sorted([f for f in os.listdir(APP_DIR + '/blog_posts') if
                    f[0:7].isdigit()], reverse=True)
    post_urls = [blog_post_url(p) for p in posts]

    post_titles = []
    for post in posts:
        with open(APP_DIR + '/blog_posts/' + post) as f:
            title = f.readlines()[0].replace('Title:', '').strip()

        date = datetime.strptime(post.split('_')[0], '%Y%m%d').strftime('%b %d, %Y')
        post_titles.append('[{}]  {}'.format(date, title))

    return render_template('blog.html', posts=zip(post_urls, post_titles))


@app.route('/photos', strict_slashes=False)
def photos():
    return render_template('photos.html')


@app.route('/projects', strict_slashes=False)
def projects():
    return render_template('soon.html')
    # return render_template('projects.html')


def verify_hash(request_body, header_value):
    h = hmac.new(config.repo_secret, request_body, hashlib.sha1)
    return hmac.compare_digest(bytes('sha1=' + h.hexdigest()),
                               bytes(header_value))


@app.route('/regenerate-climbing-logs', methods=['POST'])
def regen_logs():
    header_value = request.headers.get('X-Hub-Signature')
    request_body = request.get_data()

    if verify_hash(request_body, header_value):
        repo = git.Repo(config.climbing_repo)
        o = repo.remotes.origin
        o.pull()

        subprocess.call(['python', config.climbing_repo + 'generate-log.py',
                         '--input', config.climbing_repo + 'data/climbing-data.txt',
                         '--output', config.web_dir + 'climbing-log',
                         '--title', 'nil.bz | Climbing Log'])
        subprocess.call(['python', config.climbing_repo + 'generate-log.py',
                         '--ferrata',
                         '--input', config.climbing_repo + 'data/ferrata-data.txt',
                         '--output', config.web_dir + 'ferrata-log',
                         '--title', 'nil.bz | Ferrata Log'])

        shutil.copy(config.climbing_repo + 'css/log.css', config.web_dir)

    return redirect(url_for('home'), code=302)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=DEBUG)
