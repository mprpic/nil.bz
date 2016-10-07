Title: Fun facts on git pull

This is probably my favorite little script that I have configured to
execute with a Git alias:

<pre class="codeblock"><code class="bash">#!/bin/bash
elinks -dump randomfunfacts.com | sed -n '/^| /p' | tr -d \|</code></pre>

I have this saved as `~/bin/fact` and linked to a Git alias with the
following config in my `~/.gitconfig` file:

<pre class="codeblock"><code class="ini">[alias]
    p = !~/bin/fact && git pull</code></pre>

Each time I pull updates in any repository, it takes just enough time to
complete for me to read a random fun fact:

<pre class="codeblock"><code class="bash">]$ git p
 Every time you lick a stamp, you're consuming 1/10 of a calorie.
Current branch master is up to date.</code></pre>