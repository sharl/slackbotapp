# -*- coding: utf-8 -*-
import subprocess


class call:
    """天気<観測地点> [tenki.jpの2週間天気URL] : 天気予報を表示 [登録]"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        prefix = '天気'
        if text.startswith(prefix) and item.get('bot_id') is None:
            loc = text.replace(prefix, '').strip()
            tenkijp = ''
            if ' ' in loc:
                loc, url = loc.split()
                url = url.strip('<>')
                print(loc, url)
                tenkijp = subprocess.check_output(['tenkijp', loc, url]).decode('utf8').strip()
            else:
                tenkijp = subprocess.check_output(['tenkijp', loc]).decode('utf8').strip()

            if not tenkijp:
                return

            client.web_client.chat_postMessage(
                username=loc + 'の' + prefix,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=tenkijp,
                thread_ts=thread_ts,
            )
