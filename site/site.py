#
# Static site generator; runs hourly via cron
#

import os
import shutil
import logging
from datetime import datetime

from jinja2 import Environment, FileSystemLoader
from markdown import Markdown

TEMPLATE_DIR = './templates'
SITE_TEMPLATES = os.path.join(TEMPLATE_DIR, 'site')
COMMON_TEMPLATES = os.path.join(TEMPLATE_DIR, 'common')
BLOG_TEMPLATES = os.path.join(TEMPLATE_DIR, 'blog')
BLOG_POSTS_DIR = './blog_posts'

WORDS_PER_MINUTE = 200  # reading speed average
WORD_LENGTH = 5.1  # word length average (en_US)

log = logging.getLogger(__name__)
jinja_env = Environment(loader=FileSystemLoader([SITE_TEMPLATES, COMMON_TEMPLATES, BLOG_TEMPLATES]))


def render_templates():

    templates = os.listdir(SITE_TEMPLATES)

    for template in templates:
        rendered_template = jinja_env.get_template(template).render()

        with open(os.path.join('./html', template), 'w') as f:
            f.write(rendered_template)


def estimate_reading_time(text):
    word_count = len(text) / WORD_LENGTH
    time = round(word_count / WORDS_PER_MINUTE)

    if time < 2:
        return '1 minute'
    else:
        return f'{time} minutes'


def render_blog_posts():

    md = Markdown()

    # Blog posts are Markdown files starting with a date followed by an
    # underscore; sort by newest first
    post_files = [f for f in os.listdir(BLOG_POSTS_DIR) if
                  f[0:7].isdigit() and f[8] == '_' and f.endswith('.md')]
    post_files.sort(reverse=True)

    posts = []
    for post in post_files:

        # Split the file name into a date and a URL
        post_date, url = post.rstrip('.md').split('_')
        post_date = datetime.strptime(post_date, '%Y%m%d')

        with open(os.path.join(BLOG_POSTS_DIR, post)) as f:
            content = f.readlines()

        # First line is the post's title
        post_title, content = content[0].strip(), ''.join(content[1:]).strip()

        site_title = 'Blog - ' + post_title
        reading_time = estimate_reading_time(content)

        content = md.convert(content)
        posts.append({'content': content, 'site_title': site_title, 'post_title': post_title,
                      'post_date': post_date, 'post_url': url, 'reading_time': reading_time})

    # Render blog posts
    for post in posts:
        rendered_template = jinja_env.get_template('post.html').render(**post)
        with open(os.path.join('./html/blog/', post['post_url'] + '.html'), 'w') as f:
            f.write(rendered_template)

    # Render blog list
    blog_list = jinja_env.get_template('list.html').render(posts=posts)
    with open('./html/blog.html', 'w') as f:
        f.write(blog_list)


if __name__ == '__main__':
    # Scrap previous HTML files
    shutil.rmtree('./html', ignore_errors=True)

    # Create new HTML directory
    if not os.path.exists('./html'):
        os.makedirs('./html/blog')

    render_templates()
    render_blog_posts()
