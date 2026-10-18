# -*- coding: utf-8 -*-
import sys

import requests

url = 'https://hatsusaburo.pages.dev/routes/index.json'
ways = sys.argv[1:] if len(sys.argv) > 1 else ['^jr']

with requests.get(url, timeout=10) as r:
    data = r.json()
    for d in data['routes']:
        _id = d.get('id')
        company = d.get('company')
        for way in ways:
            sway = way.startswith('^') and _id.startswith(way.removeprefix('^'))
            if sway or (way in _id) or (company and way.upper() in company):
                print(d.get('name', '').split('\u30fb')[-1], company, _id)
