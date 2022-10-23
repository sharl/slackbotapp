# -*- coding: utf-8 -*-
class call:
    def __init__(self, client, req, options=None, caches={}):
        text = req.payload["event"]["text"]
        user = req.payload['event']['user']
        channel = req.payload["event"]["channel"]

        if text == "hello":
            client.web_client.chat_postMessage(
                text=f'hi, <@{user}>',
                channel=channel,
            )
