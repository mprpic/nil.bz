Generating DH primes with limited resources

If you own a small VPS that runs your personal website, chances are that
your CPU is collecting dust most of the time unless you get a ton of
traffic (not my case). Any time I run `top` or `uptime`, the CPU load
average for the last 15 minutes is anywhere between 0.0 to a staggering
0.06. What a waste...

So what can we do with all these wasted resources? We could try computing
Diffie-Hellman parameters! In reality, these are just encoded prime
numbers. They are often hardcoded in various applications that perform a
[Diffie-Hellman key
exchange](https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange)
between a client and a server component. In a key exchange, the larger the
prime that is used, the more computationally intensive it is to solve the
discrete logarithm problem that would allow you to uncover the secret key.

In October 2015, the [Logjam](https://weakdh.org/) attack publicized the
fact that a lot of the traffic on the Internet uses a handful of known primes.
Precomputing data for a few of these primes would allow you to decrypt much
of that traffic with ease. One way to avoid this is to use new primes of
large size. Computing these is not an easy task but we could rely on other
sources to acquire them. A collection of DH primes has been started in
[this](https://github.com/RedHatProductSecurity/Diffie-Hellman-Primes/)
GitHub repository. The next problem is to actually prove that the primes
added in this repository are actual primes. But that's a topic for another
blog post.

So how do you generate a DH prime? The easiest option is to use the
`openssl` command, for example:

<pre class="codeblock"><code class="bash">#!/bin/bash
for i in $(seq 1 1000);
do
  openssl dhparam 4096 -text >> /home/user/dhprimes/$i 2> /dev/null
done</code></pre>

Naturally, when you run this, it will eat up 100% of your CPU. Generating a
4096-bit prime (as shown in example above) can take around two hours,
depending on your CPU.

Since you probably want to use your VPS for tasks other than computing
primes, you should limit the `openssl` command to only use a certain
percentage of the CPU time. One way to do this is to adjust the "niceness"
of the process running `openssl` to 19 (least favorable to the process).
That way, when any other process has to use the CPU, the `openssl` one will
happily give up its CPU time.

This may not be ideal when you want to assure that CPU time is available to
other tasks immediately, not only after the scheduler takes it from
`openssl` and gives it to the other processes needing it. One way to do
this is to set a hard limit on the amount of CPU time our script uses.
`systemd` provides us with a nice option,
[`CPUQuota`](https://www.freedesktop.org/software/systemd/man/systemd.resource-control.html#CPUQuota=),
that allows us to do just that. We can create a service unit file such as:

<pre class="codeblock"><code class="ini">[Unit]
Description=Compute DH primes

[Service]
User=user
ExecStart=/home/user/dhprimes/generate_primes.sh
CPUQuota=10%

[Install]
WantedBy=multi-user.target</code></pre>

Another advantage of using `systemd` service files is that we can run the
script as a service, without having to use `screen` or other solutions that
allow you to run jobs in the background.

When we start the service above, `top` starts reporting these values:

<pre class="codeblock"><code>PID   USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
23337 user      20   0   40552   2548   1900 R 10.0  0.5   0:01.85 openssl</code></pre>

So now our CPU is at least a little busy doing something useful. Once you
generate enough primes, don't be shy to submit a pull request in the GitHub
repo linked above. I started the above service on my VPS to generate
8192-bit primes and after running for three days, I discovered a single
prime! Granted it's a VPS with a 1.8 GHz processor, of which only 10% is
used towards the prime generation.
