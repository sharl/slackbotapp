#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import importlib

from libsixel.encoder import Encoder

from modules import Caches

caches = Caches()


class WebClient:
    def __init__(self):
        pass

    def chat_postMessage(self, **kwargs):
        print(kwargs)

    def files_upload_v2(self, **kwargs):
        encoder = Encoder()
        encoder.encode(kwargs.get('file'))


class Client:
    def __init__(self):
        self.web_client = WebClient()


class Req:
    def __init__(self):
        self.payload = {
            'event': {
                'text': '',
                'channel': 'test',
            }
        }


client = Client()
req = Req()

module = sys.argv[1].replace('.py', '').replace('/', '.')
m = importlib.import_module(f'{module}')
req.payload['event']['text'] = sys.argv[2]

m.call(client, req, caches=caches)
