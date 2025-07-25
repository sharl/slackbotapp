# -*- coding: utf-8 -*-
import copy
import os
import time
from random import sample

DATATXT = 'bingo.txt'
BINGOES = []
MAXLEN = 0
if not BINGOES:
    with open(DATATXT) as fd:
        BINGOES = fd.read().strip().split('\n')
        for key in BINGOES:
            if len(key) > MAXLEN:
                MAXLEN = len(key)

DATABASE = 'bingo.csv'
CLOSED = '0'
OPENED = '1'
WIDTH = HEIGHT = 5
LINE = '+' + ('-' * ((MAXLEN * 2 + 1) * WIDTH - 1)) + '*'
QUOTE = '```'
# judgement desuno
#  0  1  2  3  4
#  5  6  7  8  9
# 10 11 12 13 14
# 15 16 17 18 19
# 20 21 22 23 24
BINGO = [OPENED]
REACH = [CLOSED, OPENED, OPENED, OPENED, OPENED]
# \ left top to right bottom
LTRB = slice(0, WIDTH * HEIGHT, WIDTH + 1)
# / right top to lefe bottom
RTLB = slice(WIDTH - 1, WIDTH * HEIGHT, WIDTH - 1)


class call:
    """ビンゴ: ビンゴゲームにエントリーします (テスト中)"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        user_id = item.get('user')
        username = caches.display_names.get(user_id)
        text = item['text']
        channel = item['channel']
        thread_ts = item.get('thread_ts')
        # それぞれの成立回数
        self.bingo = {}
        self.reach = {}

        keyword = 'ビンゴ'
        message = None
        if text == keyword:
            message = self.entryBingo(user_id, username)
        elif text and item.get('bot_id') is None:
            # すべての発言に対して実行(たぶん遅い)
            start = time.time()

            data = self.loadCards()
            newdata = copy.deepcopy(data)

            lines = []
            for _id in newdata:
                _card, _open = newdata[_id]
                _uid, _name = _id.split(',', 1)
                if _name not in self.bingo:
                    self.bingo[_name] = 0
                if _name not in self.reach:
                    self.reach[_name] = 0

                idx = None
                for i, d in enumerate(_card):
                    if d in text:
                        idx = i
                        break
                if idx is not None:
                    if _open[idx] == CLOSED:
                        _open[idx] = OPENED

                        # update DATABASE
                        newdata[_id] = [_card, _open]

                        # make card result
                        lines.append(f'{_name}さんの{_card[idx]}が開きました')
                        lines += self.showCard(_card, _open)

                        # judgement desuno
                        # horizontal
                        for y in range(HEIGHT):
                            a = _open[slice(y * HEIGHT, y * HEIGHT + WIDTH)]
                            _l = list(set(a))
                            s = sorted(a)
                            if s == REACH:
                                self.reach[_name] += 1
                                lines.append(f'{_name}さん {self.reach[_name]} リーチです')
                            if _l == BINGO:
                                self.bingo[_name] += 1
                                lines.append(f'{_name}さん {self.bingo[_name]} ビンゴです')
                        # vertical
                        for x in range(WIDTH):
                            a = _open[slice(x, WIDTH * HEIGHT, HEIGHT)]
                            _l = list(set(a))
                            s = sorted(a)
                            if s == REACH:
                                self.reach[_name] += 1
                                lines.append(f'{_name}さん {self.reach[_name]} リーチです')
                            if _l == BINGO:
                                self.bingo[_name] += 1
                                lines.append(f'{_name}さん {self.bingo[_name]} ビンゴです')
                        # \ left top to right bottom
                        a = _open[LTRB]
                        _l = list(set(a))
                        s = sorted(a)
                        if s == REACH:
                            self.reach[_name] += 1
                            lines.append(f'{_name}さん {self.reach[_name]} リーチです')
                        if _l == BINGO:
                            self.bingo[_name] += 1
                            lines.append(f'{_name}さん {self.bingo[_name]} ビンゴです')
                        # / right top to lefe bottom
                        a = _open[RTLB]
                        _l = list(set(a))
                        s = sorted(a)
                        if s == REACH:
                            self.reach[_name] += 1
                            lines.append(f'{_name}さん {self.reach[_name]} リーチです')
                        if _l == BINGO:
                            self.bingo[_name] += 1
                            lines.append(f'{_name}さん {self.bingo[_name]} ビンゴです')

                        message = '\n'.join(lines)

            # update DATABASE
            if newdata != data:
                self.updateCards(newdata)

            end = time.time()
            print(f"bingo took {end - start:f} s")

        elif not text and item.get('bot_id') is None:
            data = self.loadCards()
            for _id in data:
                _card, _open = data[_id]
                lines = [_id.split(',')[1]]
                lines += self.showCard(_card, _open)
                print('\n'.join(lines))

        # is bingo?
        bingo = 0
        for member in self.bingo:
            if self.bingo[member]:
                message += f'\n{member}さんおめでとうございます'
                bingo += 1
        if bingo:
            os.unlink(DATABASE)

        if message:
            client.web_client.chat_postMessage(
                username=keyword,
                icon_emoji=caches.icon_emoji,
                channel=channel,
                text=message,
                thread_ts=thread_ts,
            )

    def loadCards(self):
        cards = {}
        if os.path.isfile(DATABASE):
            with open(DATABASE) as fd:
                lines = fd.read().strip().split('\n')
                for line in lines:
                    tmp = line.split(',')
                    _id, _name, _card, _open = tmp[0], tmp[1], tmp[2].split(), tmp[3].split()
                    if _id not in cards:
                        cards[f'{_id},{_name}'] = [_card, _open]
        return cards

    def updateCards(self, cards):
        lines = []
        for ids in cards:
            _id, _name = ids.split(',', 1)
            _card, _open = cards[ids]

            lines.append(f'{_id},{_name},{" ".join(_card)},{" ".join(_open)}')
        with open(DATABASE, 'w') as fd:
            fd.write('\n'.join(lines))

    def entryBingo(self, user_id, username):
        data = self.loadCards()
        _id = f'{user_id},{username}'
        if _id not in data:
            # new entry
            # user_id,username,sample(AMEDAS, 25),0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0
            locs = sample(BINGOES, WIDTH * HEIGHT)
            center = (WIDTH * HEIGHT - 1) // 2
            # center is free
            locs[center] = 'なんでも'
            # center FREE is opened
            flags = [CLOSED for _ in range(WIDTH * HEIGHT)]
            flags[center] = OPENED

            # update DATABASE
            data[f'{user_id},{username}'] = [locs, flags]
            self.updateCards(data)

            message = f'{username}さんのエントリーが完了しました'
        else:
            _card, _open = data[_id]
            lines = [f'{username}さんのビンゴカードです']
            lines += self.showCard(_card, _open)
            message = '\n'.join(lines)

        return message

    def showCard(self, _card=[], _open=[]):
        lines = []
        lines.append(QUOTE)
        for y in range(HEIGHT):
            line = '|'
            for x in range(WIDTH):
                i = y * HEIGHT + x
                loc = _card[i] if _open[i] == OPENED else ''
                _l = len(loc)
                s = '\u3000' * (MAXLEN - _l)
                line += f'{loc}{s}|'
            lines.append(line)
        # lines.append(LINE)
        lines.append(QUOTE)

        return lines
