Add text

<pre class="codeblock"><code class="python">@app.route('/payload', methods=['POST'])
def process_payload():
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