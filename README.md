# chatstrmr
chatstrmr reads weechat IRC logs from stdin and serves them to the web.

It can embed IRC logs into OBS with decent formatting for streaming/recording.

&nbsp;

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

&nbsp;

If you insist on running this program, you probably want to do something like:  

    tail -s.1 -F ~/.weechat/logs/irc.znc.\#wikimedia-operations.weechatlog' \
        | gunicorn -w1 --threads 64 app:app

The `-w1` is *very* important: you need exactly one worker process.

You probably also want to do

    /set logger.file.flush_delay 0

in your Weechat.

## dependencies

    sudo apt install python3-flask gunicorn
