# -*- coding: utf-8 -*-
import base64
import datetime as dt
import io
import os
import re

from ddgs import DDGS
import ollama
import requests

from modules import postMessage

CONFIG = '.ollama-model'


class call:
    """はむ、<質問> : Ollama を使用して検索結果を元に回答を生成します"""
    def __init__(self, client, req, options=None, caches={}):
        item = req.payload['event']
        text = item['text']
        channel = item['channel']
        ts = item.get('ts')
        thread_ts = item.get('thread_ts')

        def pre(text):
            return f'```\n{text}\n```'

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

        def post(text):
            if text:
                postMessage(
                    client,
                    caches.username,
                    caches.icon_emoji,
                    channel,
                    text,
                    thread_ts=thread_ts,
                )

        def search_web(query: str, max_results: int = 5):
            engines = 'brave duckduckgo google wikipedia'.split()
            results = []
            for engine in engines:
                try:
                    with DDGS() as ddgs:
                        r = list(ddgs.text(
                            query,
                            backend=engine,
                            region='jp-jp',
                            safesearch='off',
                            max_results=max_results)
                        )
                        results += r
                except Exception:
                    pass
            return [f"Title: {r['title']}\nSnippet: {r['body']}" for r in results]

        def summarize_with_ollama(query: str, contexts: list, images: list = []):
            context_text = '\n\n'.join(contexts)
            name = caches.username
            now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime('%Y年%m月%d日 %H時%M分')
            prompt = f'{query}'
            if os.path.exists('PROMPT.md'):
                with open('PROMPT.md', encoding='utf-8') as fd:
                    promptf = fd.read()
                    prompt = promptf.format(**locals())
            try:
                response = ollama.generate(
                    model=self.model,
                    prompt=prompt,
                    images=images,
                    options={'temperature': 0},
                )
                return response.get('response', 'わかりません')
            except Exception as e:
                return f'Ollamaエラー: {str(e)}'

        def search_and_summarize(query: str, images: list) -> str:
            search_results = search_web(query, max_results=10)
            if not search_results:
                return 'よくわかりません'

            summary = summarize_with_ollama(query, search_results, images)
            return summary

        prefix = '{}:'.format(caches.username)
        if options:
            prefix = options.get('prefix', str())

        if text.startswith(prefix) and item.get('bot_id') is None:
            prompt = text.replace(prefix, '').strip()
            if not prompt:
                return

            self.model = str()
            with open(CONFIG) as fd:
                self.model = fd.read().strip()

            print(f'>>> now model {self.model}')

            # List Local Models
            if prompt == 'モデル一覧':
                _models = ollama.list()['models']
                models = {}
                for _model in _models:
                    models[_model.model] = [
                        f"{_model.size / (1024 * 1024 * 1024):.1f}G",
                        _model.details.parameter_size,
                        _model['details']['quantization_level'],
                    ]

                name_len = max([len(name) for name in models])
                size_len = max([len(models[name][0]) for name in models])
                qsize_len = max([len(models[name][1]) for name in models])

                lines = [f'  {"NAME":<{name_len}}  {"SIZE":<{size_len}}  {"QSIZE":<{qsize_len}}  TYPE']
                for name in models:
                    lines.append(f'{"*" if name == self.model else " "} {name:<{name_len}}  {models[name][0]:<{size_len}}  {models[name][1]:<{qsize_len}}  {models[name][2]}')

                post(pre('\n'.join(lines)))
                return

            # Change Model
            c_prefix = 'モデルを'
            c_suffixes = ('に変えて', 'に変更して', 'にして')
            if prompt.startswith(c_prefix) and prompt.endswith(c_suffixes):
                _model = prompt.replace(c_prefix, '')   # .replace(c_suffixs, '').strip()
                for s in c_suffixes:
                    if _model.endswith(s):
                        _model = _model.replace(s, '')
                _model = _model.strip()

                if ':' not in _model:
                    post('モデルには : を含める必要があります')
                    return

                if ollama.show(_model):
                    if _model != self.model:
                        with open(CONFIG, 'w') as fd:
                            fd.write(_model + '\n')
                            post(f'モデルを {_model} に変更しました')
                            print(f'>>> new model {_model}')
                    else:
                        post(f'現在のモデルが {_model} です')
                else:
                    post(f'{_model} はありません')
                return

            # Generate an answer
            reactions_add('loading')

            images = list()
            m = re.search(r'<(https?://.+)\|?.*?>', text)
            if m:
                for url in m.groups():
                    if url.startswith('http'):
                        with requests.get(url) as r:
                            image_bytes = io.BytesIO(r.content)
                            encoded = base64.b64encode(image_bytes.getvalue()).decode('utf-8')
                            images.append(encoded)
                            prompt = prompt.replace(f'<{url}>', '')

            answer = search_and_summarize(prompt, images)

            # **hoge** -> hoge
            answer = answer.replace('**', '')
            post(answer)

            reactions_remove('loading')

            return
