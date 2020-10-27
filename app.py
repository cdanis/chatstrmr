#!/usr/bin/env python3
"""chatstrmr reads weechat IRC logs from stdin and serves them to the web.

It can embed IRC logs into OBS with decent formatting for streaming/recording.

⚠️ WARNING! ⚠️
☢️ 😱 DO NOT USE THIS PROGRAM. 😱 ☢️
This program is not a program of honor.

No highly esteemed function is executed here.

What is here is dangerous and repulsive to us.

The danger is still present, in your time, as it was in ours,
without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.

This program is best shunned and left unused (but it is free software,
and you are welcome to redistribute it under certain conditions).
😱 ☢️ DO NOT USE THIS PROGRAM. ☢️ 😱

If you insist on running this program, you probably want to do something like:
tail -s.1 -F ~/.weechat/logs/irc.znc.\\#wikimedia-operations.weechatlog' \\
    | gunicorn -w1 --threads 64  app:app

The -w1 is *very* important: you need exactly one worker process.

You probably also want to do
    /set logger.file.flush_delay 0
in your Weechat.
"""

__version__ = '0.0.1'
__author__ = "Chris Danis"
__email__ = "cdanis@gmail.com"
__repository__ = "https://github.com/cdanis/chatstrmr"
__license__ = "AGPLv3"
__copyright__ = """
Copyright © 2020 Chris Danis

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import collections
import fileinput
import itertools
import json
import queue
import threading

from flask import Flask, Response, render_template


class MessageAnnouncer:
    # inspired by https://github.com/MaxHalford/flask-sse-no-deps
    def __init__(self):
        self._listeners = collections.deque()
        self._listeners_lock = threading.Lock()

    def listen(self):
        rv = queue.Queue(maxsize=10)
        with self._listeners_lock:
            self._listeners.append(rv)
        return rv

    def announce(self, msg):
        with self._listeners_lock:
            for i in reversed(range(len(self._listeners))):
                try:
                    self._listeners[i].put_nowait(msg)
                except queue.Full:
                    del self._listeners[i]


announcer = MessageAnnouncer()


# TODO announcer should probably maintain this
lastlines = collections.deque(maxlen=500)
lastlines_lock = threading.Lock()
lastlines_thread = None


def parse(line):
    (timestamp, who, msg) = line.strip().split('\t', maxsplit=3)
    timestamp = timestamp.split(' ')[1]
    if any(needle in who for needle in ['stashbot', '--']) or not who:
        return None
    if 'logmsgbot' not in who:
        msg = f"<{who}> {msg}"
    if 'icinga-wm' in who:
        msg = msg.split('https://', maxsplit=1)[0]
    data = dict(time=timestamp, who=who, msg=msg)
    print(data)
    return 'data: ' + json.dumps(data) + "\n\n"


def readlines_fn():
    # https://i.imgur.com/obIcqlF.gif
    global lastlines, lastlines_lock, announcer
    for line in fileinput.input('-'):
        event = parse(line)
        if event:
            announcer.announce(event)
            with lastlines_lock:
                lastlines.append(event)


def create_app():
    app = Flask(__name__)

    lastlines_thread = threading.Thread(name="lastlines", target=readlines_fn)
    lastlines_thread.start()

    return app


app = create_app()


@app.route('/peek')
def peek():
    with lastlines_lock:
        return repr(lastlines) + "\n"


def stream():
    messages = announcer.listen()
    while True:
        msg = messages.get()
        yield msg


def backlog():
    with lastlines_lock:
        for line in lastlines:
            yield line


@app.route('/listen', methods=['GET'])
def listen():
    return Response(stream(), mimetype='text/event-stream')


@app.route('/listenmore')
def listenmore():
    def superstream():
        for i in itertools.chain(backlog(), stream()):
            yield i
    return Response(superstream(), mimetype='text/event-stream')


@app.route('/')
def index():
    return render_template('index.html')
