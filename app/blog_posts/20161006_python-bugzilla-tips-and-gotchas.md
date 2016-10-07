Title: python-bugzilla tips and gotchas

The [`python-bugzilla`](https://github.com/python-bugzilla/python-bugzilla)
library is used for interaction with Bugzilla. It's not tied to any
specific Bugzilla instance and works across various versions. It's not the
most intuitive library to use and the documentation is pretty much
non-existent. What follows is a couple of gotchas that I've been bitten by
when using this library.

As a prerequisite, let's initialize a Bugzilla object to work with
throughout the examples:

<pre class="codeblock"><code class="python">>>> from bugzilla import RHBugzilla
>>> url = 'https://bugzilla.redhat.com'
>>> bz = RHBugzilla(url=url, user=u, password=p)</code></pre>

Note: in these examples I'm using Red Hat's Bugzilla instance but they
should apply to any other Bugzilla instance out there.

## Including specific fields

Let's say you want to query your Bugzilla instance for a set of bugs.
We can do that with the `getbugs()` call:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; BZ.getbugs([1291176, 1312219])
[&lt;Bug #1291176 on https://bugzilla.redhat.com/xmlrpc.cgi at 0x2b50f50&gt;,
&lt;Bug #1312219 on https://bugzilla.redhat.com/xmlrpc.cgi at 0x2b50190&gt;]</code></pre>

The returned bugs include a whole lot of information that we may not need
(you can run `dir()` on one of the returned bugs to see all the data it
includes). This is especially important if you're trying to pull
information for a large set of bugs. We can limit the data that is returned
with the `include_fields` parameter:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; res = bz.getbugs([1291176, 1312219], include_fields=['id', 'status'])
&gt;&gt;&gt; res[0].status
'CLOSED'</code></pre>

Gotcha #1: you may be inclined to think that if you only care about the
statuses of the queried bugs, you can limit the `include_fields` parameter
to only return `status`. However, doing so results in a not so helpful
`KeyError: 'id'` error. This is because the `id` field is a
mandatory value.

Gotcha #2: if for some reason you try to access an attribute of a bug that
has not been originally queried for, you may be surprised that the
operation succeeds and the value is returned. What's the point of
`include_fields` then you may ask. The fact is that when you query a bug
for an attribute it doesn't have loaded, it requests it from Bugzilla for
you (along with the rest of the attributes) and returns it as if nothing
happened:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; res = bz.getbugs([1291176, 1312219], include_fields=['status', 'id'])
&gt;&gt;&gt; 'priority' in dir(res[0]), len(dir(res[0]))
(False, 52)
&gt;&gt;&gt; res[0].priority
'high'
&gt;&gt;&gt; 'priority' in dir(res[0]), len(dir(res[0]))
(True, 126)</code></pre>

Lesson learned: always double check that you're not using any attributes
that you haven't initially requested. Otherwise you'll trigger a separate
request for each bug when you access an unknown attribute.

## Requesting a bug's comment #0

If you're interested in querying your Bugzilla instance for comment #0 (the
initial comment, also called Description) for a large number of bugs, it's
smart to do so with a single request rather than iterating over a list of
bugs one by one. The `get_comments()` function allows us to do just that:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; res = bz.get_comments([1291176, 1312219])
&gt;&gt;&gt; type(res)
<type 'dict'></code></pre>

Note that the returned object is a dictionary with two keys: `bugs` and
`comments`. I have yet to figure out what the `comments` dictionary is
supposed to contain (hint: not comments, those are in `bugs`). The `bugs`
dictionary contains the queried bugs and their comments; each comment is
accompanied by its metadata such as creation time, author, text, etc.
To get to comment #0, use:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; res['bugs']['1291176']['comments'][0]['text']
'The following flaw, reported by...</code></pre>

Gotcha #3: Curiously, bugs exist that do not have comment #0! For example,
a bug in Novell's Bugzilla instance:
[873992](https://bugzilla.novell.com/show_bug.cgi?id=873992). Thus, you
should always check if the returned `res['bugs']` is an empty dictionary
before trying to extract any comments out of it.

So since we have a fancy function that returns comments for a list of bugs,
let's try and run it on a thousand bugs! Uh, no... I quickly learned that
literally no Bugzilla instance can handle a response that big and even if
it could, it would take a long long time. If you find yourself wanting to
pull a large number of comments, you can split out your load over several
requests (adjust `bulk` as needed):

<pre class="codeblock"><code class="python">bulk = 100
for idx in range(0, len(bugs), bulk):
    res = bz.get_comments(bugs[idx:idx + bulk])['bugs']</code></pre>

(Side note: please be mindful that you don't hammer a Bugzilla instance of
your choice with non-stop requests that have ridiculously large responses
like the one above)

## Query building

If you need to build out a very specific bug query, it helps if you can use
the web UI to do this. You may end up with a list of bugs and pretty long
URL. Now, if you want to use that same query in a script, you can use a
handy `url_to_query` method to get the dictionary representation of that
query:

<pre class="codeblock"><code class="python">&gt;&gt;&gt; url = 'https://bugzilla.redhat.com/buglist.cgi?bug_status=NEW&classification=Red%20Hat&component=openssl&product=Red%20Hat%20Enterprise%20Linux%207&query_format=advanced'
&gt;&gt;&gt; bz.url_to_query(url)
{'bug_status': 'NEW', 'product': 'Red Hat Enterprise Linux 7', 'component': 'openssl',
'query_format': 'advanced', 'classification': 'Red Hat'}
&gt;&gt;&gt; bz.query(bz.url_to_query(url))
[&lt;Bug #1255248...</code></pre>

Similarly, you can use the `build_query()` function to build out a
dictionary that can be passed to the query method. Very handy!