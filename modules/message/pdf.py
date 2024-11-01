# -*- coding: utf-8 -*-
import os
import re
import io
from tempfile import mkstemp

import requests
import pypdfium2 as pdfium


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
                    client.web_client.files_upload_v2(
                        username=caches.username,
                        icon_emoji=caches.icon_emoji,
                        channel=channel,
                        file=outfile,
                        title='image.png',
                        thread_ts=thread_ts,
                    )
                    os.unlink(outfile)
