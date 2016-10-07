Title: Verifying payloads from GitHub webhooks in Flask

When receiving payload from GitHub webhooks it's a good idea to validate
them before taking any action. This assures that your application does not
accept payloads other than those sent by GitHub. Whitelisting GitHub's IP
addresses is one potion but validating a secret token that's configured in
a GitHub webhook is much easier.

The GitHub documentation provides a nice
[example](https://developer.github.com/webhooks/securing/#validating-payloads-from-github)
of how this is done in Ruby. In Python's Flask, the code is very similar:

<pre class="codeblock"><code class="python">import hmac
import hashlib

@app.route('/regenerate-documentation', methods=['POST'])
def regenerate_docs():
    header_value = request.headers.get('X-Hub-Signature')
    request_body = request.get_data()

    if verify_hash(request_body, header_value):
        print('Success!')
    else:
        return abort(500)

def verify_hash(request_body, header_value):
    h = hmac.new(os.environ('SECRET_TOKEN'), request_body, hashlib.sha1)
    return hmac.compare_digest(bytes("sha1=" + h.hexdigest()),
                               bytes(header_value))</code></pre>

In this example, the secret token is defined in the `SECRET_TOKEN`
environment variable. The request coming from GitHub will contain the
secret token in the `X-Hub-Signature` header, along with a ton of other
useful data. Now all that's left is to compute the hash with Python's
[`hmac`](https://docs.python.org/3/library/hmac.html#hmac.new) module:

<pre class="codeblock"><code class="python">hmac.new(key, msg=None, digestmod=None)</code></pre>

If the hashes match, the request is valid and your application can trigger
whatever action it is configured to do.