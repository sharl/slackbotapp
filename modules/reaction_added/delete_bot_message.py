# -*- coding: utf-8 -*-
class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']

        reaction = 'see_no_evil'
        if isinstance(options, dict) and options.get('reaction'):
            reaction = options['reaction']
        if item['reaction'] == reaction:
            _channel = item['item']['channel']
            _ts = item['item']['ts']
            client.web_client.chat_delete(
                channel=_channel,
                ts=_ts,
            )
