# -*- coding: utf-8 -*-
import os
import re
import io
from tempfile import mkstemp

import requests
import pypdfium2 as pdfium

from modules import uploadFile


class call:
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')

        m = re.search(r'<(https?://.+)\|?.*?>', text)
        if m:
            url = m.group(1).split('|')[0]
            if url.endswith('.pdf'):
                print('try', url)
                user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
                headers = {
                    'User-Agent': user_agent
                }
                try:
                    with requests.get(url, headers=headers, timeout=10) as r:
                        _, outfile = mkstemp(suffix='.png')
                        pdf = pdfium.PdfDocument(io.BytesIO(r.content))
                except Exception as e:
                    print(e)
                    return

                # render page
                bitmap = pdf[0].render()    # scale=1
                image = bitmap.to_pil()
                image.save(outfile)
                uploadFile(
                    client,
                    caches.username,
                    caches.icon_emoji,
                    channel,
                    'image.png',
                    outfile,
                    thread_ts=thread_ts,
                )
                os.unlink(outfile)
