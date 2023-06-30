## Local Setup

```
caddy start --config Caddyfile
```

Navigate to http://localhost:8080/ to view the site.

Watch for changes in local static files and automatically rebuild:

```
# requires: dnf install entr
$ find . -name '*.html' -o -name '*.md' -not -path './html/*' | entr python3 site.py
```
