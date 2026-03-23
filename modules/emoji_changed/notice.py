# -*- coding: utf-8 -*-
from modules import postMessage


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        subtype = item['subtype']

        # item {'type': 'emoji_changed', 'subtype': 'add', 'name': 'secoma', 'value': 'https://emoji.slack-edge.com/TGKMYT9GR/secoma/219e765e1a840e31.png', 'event_ts': '1731668413.009400'}
        # item {'type': 'emoji_changed', 'subtype': 'remove', 'names': ['secoma'], 'event_ts': '1731668103.009100'}

        message = ''
        if subtype == 'add':
            name = item['name']
            message = f'emoji {name} :{name}: added'
        elif subtype == 'remove':
            names = item['names']
            message = f'emoji {" ".join(names)} deleted'

        channel_id = None
        channel_name = options.get('channel')
        if channel_name is None:
            if caches.generals:
                channel_id = caches.generals[0].keys()[0]
        else:
            for c_id in caches.channel_ids:
                c_name = caches.channel_ids[c_id]
                if c_name == channel_name:
                    channel_id = c_id
                    break

        postMessage(
            client,
            caches.username,
            caches.icon_emoji,
            channel_id,
            message,
        )
