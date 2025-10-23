# -*- coding: utf-8 -*-
from tempfile import mkstemp
import html
import os
import subprocess

import pyxel


def parse(mml):
    tracks = {}
    MML_PREFIX = 'MML#'

    for _l in mml.strip().splitlines():
        _track = line = ''
        _l = _l.strip()
        try:
            if _l.startswith(MML_PREFIX):
                _track, line = _l.split(' ', maxsplit=1)
            else:
                _track = MML_PREFIX + '0'
                line = _l
        except ValueError:
            pass

        # unescape
        line = html.unescape(line)

        # parse
        if _track.upper().startswith(MML_PREFIX):
            track = _track.upper().removeprefix(MML_PREFIX)
            if track.isnumeric():
                track = int(track)
            else:
                track = 0
        else:
            track = 0

        if track not in tracks:
            tracks[track] = []
        tracks[track].append(line)

    # init
    pyxel.init(0, 0)

    # reset
    for track in range(4):
        pyxel.sounds[track].mml()

    # entry sounds
    for track in tracks:
        pyxel.sounds[track].mml(' '.join(tracks[track]))

    # mixup
    pyxel.musics[0].set([0], [1], [2], [3])
    sec = pyxel.sounds[0].total_sec()
    # get temporary filename
    _, outfile = mkstemp()
    os.unlink(outfile)
    # save wav
    pyxel.musics[0].save(outfile, sec)
    # wav to mp3
    subprocess.run(f'ffmpeg -v 0 -y -i {outfile}.wav {outfile}.mp3'.split())
    os.unlink(f'{outfile}.wav')

    pyxel.quit()

    return f'{outfile}.mp3'


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
        thread_ts = item.get('thread_ts')

        keyword = 'MML'
        DESC_PREFIX = 'DESC'
        if text.startswith(keyword) and item.get('bot_id', None) is None:
            lines = []
            desc = keyword
            for line in text.removeprefix(keyword).splitlines():
                if line.strip().startswith(DESC_PREFIX):
                    desc = line.strip().removeprefix(DESC_PREFIX).strip()
                else:
                    lines.append(line.strip())
            mml = '\n'.join(lines)

            if mml.strip():
                outfile = parse(mml)
                print(__name__, outfile)
                client.web_client.files_upload_v2(
                    username=keyword,
                    icon_emoji=caches.icon_emoji,
                    channel=channel,
                    file=outfile,
                    title=desc,
                    thread_ts=thread_ts,
                )
                os.unlink(outfile)
