#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib
import json
import mimetypes
import os
import re
import sys
import tempfile

from libsixel.encoder import Encoder
import requests

from modules import Caches


def slack_emojizer():
    """
    Slack の :shortname: が反映されている 2026/09/06
    """
    slack_dict = {}
    pattern = re.compile(r':[a-zA-Z0-9_+-]+:')

    if not os.path.exists('emoji.json'):
        url = 'https://raw.githubusercontent.com/iamcal/emoji-data/refs/heads/master/emoji.json'
        with requests.get(url, timeout=10) as r:
            emoji_data = r.json()
        with open('emoji.json', 'w') as fd:
            fd.write(json.dumps(emoji_data, separators=(',', ':'), ensure_ascii=False))
    else:
        with open('emoji.json') as fd:
            emoji_data = json.loads(fd.read())

    for item in emoji_data:
        try:
            emoji_char = ''.join(chr(int(code, 16)) for code in item['unified'].split('-'))
        except (ValueError, KeyError):
            continue

        for short_name in item.get('short_names', []):
            slack_dict[f':{short_name}:'] = emoji_char

    def emojize(text: str) -> str:
        return pattern.sub(lambda m: slack_dict.get(m.group(0), m.group(0)), text)

    return emojize


emojize = slack_emojizer()
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
        print(f"{kwargs.get('username')}>\n{emojize(kwargs.get('text'))}")

        blocks = kwargs.get('blocks')
        if blocks:
            for b in blocks:
                if b.get('text'):
                    print(b['text']['text'])
                url = b.get('image_url')
                if url:
                    with requests.get(url, timeout=10) as r:
                        print(r, url)
                        with tempfile.NamedTemporaryFile(mode='wb') as t:
                            t.write(r.content)
                            self.encoder.encode(t.name)

    def files_upload_v2(self, **kwargs):
        filename = kwargs.get('file')
        mime_type = mimetypes.guess_type(filename)[0]
        print(filename, mime_type)
        if mime_type.startswith('image'):
            self.encoder.encode(filename)
        elif mime_type.startswith('audio'):
            pass

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

dummy_user_key = 'U'
caches.user_ids = {dummy_user_key: os.environ.get('UID')}
caches.display_names = {dummy_user_key: os.environ.get('USER')}

module = sys.argv[1].replace('.py', '').replace('/', '.')
m = importlib.import_module(f'{module}')
req.payload['event']['text'] = ' '.join(sys.argv[2:])
req.payload['event']['user'] = dummy_user_key

m.call(client, req, options=options.get(module.replace('modules.', ''), {}), caches=caches)
