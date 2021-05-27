## Local Setup

```
$ python site.py  # Build static files
$ podman build . -t mysite  # Build container image (only necessary after changes)
$ podman run -p 8080:8080 -d mysite  # Run site
```

Navigate to http://localhost:8080/ to view the site.

Watch for changes in local static files and automatically rebuild:

```
# requires: dnf install entr
$ find . -name '*.html' -o -name '*.md' -not -path './html/*' | entr python3 site.py
```
