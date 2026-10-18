# -*- coding: utf-8 -*-
import io
import re
import sys

if not sys.stdin.isatty():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    lines = sys.stdin.read().splitlines()

number = int(sys.argv[1]) if len(sys.argv) > 1 else 2

rpls = [
    re.compile(r'^JR'),
    re.compile(r'（.*?）'),
    re.compile(r'〈.*?〉'),
    re.compile(r'\d+条.*'),
    re.compile(r'\d+丁目.*'),
]

for line in lines:
    for rpl in rpls:
        line = re.sub(rpl, '', line)
    print(line[:number])
