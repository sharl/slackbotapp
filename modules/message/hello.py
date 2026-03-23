# -*- coding: utf-8 -*-
from modules import postMessage


class call:
    def __init__(self, client, req, options=None, caches={}):
        text = req.payload["event"]["text"]
        user = req.payload['event']['user']
        channel = req.payload["event"]["channel"]

        if text == "hello":
            postMessage(
                client,
                f'hi, <@{user}>',
                channel,
            )
