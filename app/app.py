try:
    import config
except ImportError:
    print('Config file not found; create a config.py')

import os
import hmac
import hashlib
import asyncio
import aiofiles
import aiofiles.os
from asyncio.subprocess import PIPE, STDOUT
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import git
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown

from sanic import Sanic
from sanic.response import html, json
from sanic.exceptions import NotFound, ServerError
from sanic.log import log


BLOG_DIR = './blog_posts'
TEMPLATE_DIR = './templates'
STATIC_DIR = './static'
TEMP_DIR = os.path.join(STATIC_DIR, './temp')
PHOTOS_DIR = os.path.join(STATIC_DIR, './photos')
CLIMBING_LOGS_DIR = os.path.join(STATIC_DIR, 'climbing_logs')

md = Markdown()
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

app = Sanic(__name__)
app.post_url_cache = {}
app.posts_cache = {}

#
# Static resources
#

app.static('/static', STATIC_DIR)
app.static('/temp', TEMP_DIR)
app.static('/photos', PHOTOS_DIR)
app.static('/climbing-log', os.path.join(CLIMBING_LOGS_DIR, 'climbing_log.html'))
app.static('/ferrata-log', os.path.join(CLIMBING_LOGS_DIR, 'ferrata_log.html'))

#
# Helper functions
#


def render_template(template_name, **kwargs):
    return jinja_env.get_template(template_name).render(**kwargs)


def get_blog_posts():
    posts = sorted([f for f in os.listdir(BLOG_DIR) if
                    f[0:7].isdigit() and f[8] == '_' and f.endswith('.md')],
                   reverse=True)
    post_urls = list(filter(None, [post.rstrip('.md').split('_')[1] for post in posts]))

    return posts, post_urls


def verify_hash(request_body, header_value):
    if not request_body or not header_value:
        return False

    h = hmac.new(bytes(config.repo_secret, 'utf-8'), request_body, hashlib.sha1)
    return hmac.compare_digest(bytes('sha1=' + h.hexdigest(), 'utf-8'),
                               bytes(header_value, 'utf-8'))


async def run_command(cmd):
    print('Executing:', cmd)
    p = await asyncio.create_subprocess_shell(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
    return (await p.communicate())[0]


def refresh_repo():
    try:
        repo = git.Repo(config.climbing_repo)
    except git.exc.NoSuchPathError:
        log.error('Did not find Git repo ' + config.climbing_repo)
        return json({'error': 'Did not find climbing repo: {}'.format(config.climbing_repo)}, status=400)

    try:
        repo.remotes.origin.pull()
    except git.exc.GitCommandError:
        log.error('Did not find Git repo ' + config.climbing_repo)
        return json({'error': 'Failed to pull in climbing repo: {}'.format(config.climbing_repo)}, status=400)

#
# Middleware functions
#


@app.middleware('response')
async def add_security_headers(request, response):
    response.headers = {
        # HSTS enforces the use of HTTPS
        'Strict-Transport-Security': 'max-age=31536000',

        # Disallow loading of site in a frame
        'X-Frame-Options': 'DENY',

        # Prevent browser from guessing the response's content type
        'X-Content-Type-Options': 'nosniff',

        # Prevent XSS by telling browser to block response when XSS is detected
        'X-XSS-Protection': '1; mode=block',
    }

#
# Routing
#


@app.route('/')
@app.route('/index.html')
async def home(request):
    return html(render_template('home.html'))


@app.route('/about')
async def home(request):
    return html(render_template('about.html'))


@app.route('/photos')
async def photos(request):
    return html(render_template('photos.html'))


@app.route('/projects')
async def projects(request):
    return html(render_template('soon.html'))
    # return html(render_template('projects.html'))


@app.route('/blog')
async def blog(request):
    stats = await aiofiles.os.stat(BLOG_DIR)
    last_changed = str(stats.st_mtime)

    if last_changed in app.post_url_cache:
        posts = app.post_url_cache[last_changed]

    else:
        post_files, post_urls = get_blog_posts()

        post_titles = []
        for post_file in post_files:
            async with aiofiles.open(os.path.join(BLOG_DIR, post_file)) as f:
                title = await f.readline()
                title = title.replace('Title:', '').strip()

            try:
                date = datetime.strptime(post_file.split('_')[0], '%Y%m%d').strftime('%b %d, %Y')
            except ValueError:
                log.error('Failed to parse date from blog post file ' + post_file)
                continue

            post_titles.append('[{}]  {}'.format(date, title))

        posts = list(zip(post_urls, post_titles))
        app.post_url_cache = {last_changed: posts}

    return html(render_template('blog.html', posts=posts))


@app.route('/blog/<post>')
async def blog_posts(request, post):
    post_files, post_urls = get_blog_posts()

    if post not in post_urls:
        return html(render_template('404.html'), status=404)

    post_file = post_files[post_urls.index(post)]

    stats = await aiofiles.os.stat(os.path.join(BLOG_DIR, post_file))
    last_changed = str(stats.st_mtime)

    if (
            post_file in app.posts_cache and
            app.posts_cache[post_file]['last_changed'] == last_changed
    ):
        return html(app.posts_cache[post_file]['html'])

    else:
        try:
            post_date = datetime.strptime(post_file.split('_')[0], '%Y%m%d').strftime('%A, %B %d, %Y')
        except ValueError:
            log.error('Failed to parse date from blog post file ' + post_file)
            return html(render_template('404.html'), status=404)

        async with aiofiles.open(os.path.join(BLOG_DIR, post_file)) as f:
            content = await f.readlines()

        post_title = content[0].replace('Title:', '').strip()
        site_title = 'Blog - ' + post_title

        # Converting markdown takes a long time so offload it to a separate
        # thread so app is not blocked.
        loop = asyncio.get_event_loop()
        content = ''.join(content[2:])
        content = await loop.run_in_executor(ThreadPoolExecutor(), md.convert, content)

        html_content = render_template('blog_template.html', content=content, site_title=site_title,
                                       post_title=post_title, post_date=post_date)

        app.posts_cache[post_file] = {'last_changed': last_changed, 'html': html_content}

        return html(html_content)


@app.route('/api/regenerate-climbing-logs')  # , methods=['POST'])
async def regen_logs(request):
    header_value = request.headers.get('X-Hub-Signature')
    request_body = request.body

    if not verify_hash(request_body, header_value):
        return json({'error': 'Failed to verify request payload!'})

    loop = asyncio.get_event_loop()
    error_response = await loop.run_in_executor(ThreadPoolExecutor(), refresh_repo)

    if error_response:
        return error_response

    # TODO: convert log generator into lib so we can import it instead of
    # executing ugly shell commands.
    gen_climb_log_cmd = ('/usr/bin/python {} --input {} --output {} --title "nil.bz | Climbing Log"'
                         .format(os.path.join(config.climbing_repo, 'generate-log.py'),
                                 os.path.join(config.climbing_repo, 'data/climbing-data.txt'),
                                 os.path.abspath(os.path.join(CLIMBING_LOGS_DIR, 'climbing_log.html'))))

    gen_ferrata_log_cmd = ('/usr/bin/python {} --input {} --output {} --title "nil.bz | Climbing Log" --ferrata'
                           .format(os.path.join(config.climbing_repo, 'generate-log.py'),
                                   os.path.join(config.climbing_repo, 'data/ferrata-data.txt'),
                                   os.path.abspath(os.path.join(CLIMBING_LOGS_DIR, 'ferrata_log.html'))))

    # TODO: rewrite to use aiofiles.os.sendfile (even though it looks ugly)
    copy_css_file_cmd = ('/bin/cp {} {}'.format(os.path.join(config.climbing_repo, 'css/log.css'),
                                                os.path.join(STATIC_DIR, 'css')))

    commands = [run_command(cmd) for cmd in (gen_climb_log_cmd, gen_ferrata_log_cmd, copy_css_file_cmd)]

    errors = []
    for cmd in asyncio.as_completed(commands):
        output = await cmd
        if output:
            errors.append(output.decode('utf-8'))

    if errors:
        return json({'error': 'Encountered errors: {}'.format(', '.join(errors))})
    else:
        return json({'message': 'Successfully regenerated climbing logs!'})

#
# Exception handlers
#


@app.exception(NotFound)
def not_found(request, exception):
    return html(render_template('404.html'), status=404)


@app.exception(NotFound)
def server_error(request, exception):
    return html(render_template('500.html'), status=500)


if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=config.debug, ssl=config.ssl)
