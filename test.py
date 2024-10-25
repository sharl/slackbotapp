#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import importlib
import tempfile

from libsixel.encoder import Encoder
import requests

from modules import Caches

caches = Caches()

with open('config/config.json') as fd:
    config = json.load(fd)
caches.username = config.get('name', 'bot')
caches.icon_emoji = config.get('icon_emoji', ':bot:')

mods = config.get('modules', {})
modules = {}
options = {}
docs = []

for module in sorted(mods):
    m = importlib.import_module('modules.{}'.format(module))
    modules[module] = m
    options[module] = mods[module]
    _doc = m.call.__doc__
    if _doc:
        docs.append(_doc)
    caches.doc = '\n'.join(docs)


class WebClient:
    def __init__(self):
        self.encoder = Encoder()

    def chat_postMessage(self, **kwargs):
        print(f"{kwargs.get('username')}> {kwargs.get('text')}")

        blocks = kwargs.get('blocks')
        if blocks:
            for b in blocks:
                url = b.get('image_url')
                if url:
                    r = requests.get(url)
                    with tempfile.NamedTemporaryFile(mode='wb') as t:
                        t.write(r.content)
                        self.encoder.encode(t.name)

    def files_upload_v2(self, **kwargs):
        self.encoder.encode(kwargs.get('file'))

    def reactions_add(self, **kwargs):
        print('reactions_add', kwargs)

    def reactions_remove(self, **kwargs):
        print('reactions_remove', kwargs)


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

m.call(client, req, options=options[module.replace('modules.', '')], caches=caches)
