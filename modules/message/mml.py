# -*- coding: utf-8 -*-
from tempfile import mkstemp
import base64
import html
import json
import os

import requests

TIMEOUT = 120


class call:
    """MML <MML>: MMLを解釈して音声ファイルにしてアップロードします
  - MMLの書式は https://kitao.github.io/pyxel/wasm/mml-studio/mml-commands.html
  - トラックの指定は `MML#[0-3]`
  - トラックを指定しないとデフォルトで `MML#0` になります
  - Pyxel MML Studio https://kitao.github.io/pyxel/wasm/mml-studio/"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        ts = item.get('ts')
        thread_ts = item.get('thread_ts')

        def reactions_add(name):
            client.web_client.reactions_add(
                channel=channel,
                name=name,
                timestamp=ts,
            )

        def reactions_remove(name):
            client.web_client.reactions_remove(
                channel=channel,
                name=name,
                timestamp=ts,
            )

        keyword = 'MML'
        DESC_PREFIX = 'DESC'
        if text.startswith(keyword) and item.get('bot_id', None) is None:
            lines = []
            desc = keyword
            text = html.unescape(text)
            for line in text.removeprefix(keyword).splitlines():
                if line.strip().startswith(DESC_PREFIX):
                    desc = line.strip().removeprefix(DESC_PREFIX).strip()
                else:
                    lines.append(line.strip())
            mml = '\n'.join(lines)

            reactions_add('loading')
            try:
                with requests.post('http://localhost:15678/mml', json={'mml': mml}, timeout=TIMEOUT) as r:
                    data = json.loads(r.content)
                    encoded_data = data.get('data').encode()
                    decoded_data = base64.b64decode(encoded_data.decode())

                    _, outfile = mkstemp(suffix='.mp3')
                    with open(outfile, 'wb') as fd:
                        fd.write(decoded_data)

                    client.web_client.files_upload_v2(
                        username=keyword,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        file=outfile,
                        title=desc,
                        thread_ts=thread_ts,
                    )
                    os.unlink(outfile)
            except Exception as e:
                print('Exception', e)
                reactions_add('ng')

            reactions_remove('loading')
