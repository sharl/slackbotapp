# -*- coding: utf-8 -*-
import sys

import requests


wurl = 'https://hatsusaburo.pages.dev/routes/index.json'
rurl = 'https://hatsusaburo.pages.dev/routes/{route}.json'

session = requests.Session()
ways = sys.argv[1:] if len(sys.argv) > 1 else ['jr-yamanote']

with session.get(wurl, timeout=10) as r:
    routes = r.json()['routes']
    for w in routes:
        route = w['id']
        name = w['name']
        for way in ways:
            sway = way.startswith('^') and route.startswith(way.removeprefix('^'))
            if sway or (way in route) or (way in name):
                print(route, name, file=sys.stderr)
                with session.get(rurl.format(route=route), timeout=10) as r:
                    stations = r.json()['stations']
                    for s in stations:
                        print(s['name'])
