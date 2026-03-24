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

        m = re.search(r'<(https?://.+)\|?.*?>$', text)
        if m:
            url = m.group(1).split('|')[0]
            if url.endswith('.pdf'):
                with requests.get(url, timeout=10) as r:
                    _, outfile = mkstemp(suffix='.png')
                    pdf = pdfium.PdfDocument(io.BytesIO(r.content))

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
