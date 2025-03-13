# -*- coding: utf-8 -*-
import ollama

CONFIG = '.ollama-model'


class call:
    """はむ、<質問> : Ollama を使用して回答を生成します"""
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
                client.web_client.chat_postMessage(
                    username=caches.username,
                    icon_emoji=caches.icon_emoji,
                    channel=channel,
                    text=text,
                    thread_ts=thread_ts,
                )

        prefix = '{}:'.format(caches.username)
        if options:
            prefix = options.get('prefix', str())

        if text.startswith(prefix) and item.get('bot_id') is None:
            prompt = text.replace(prefix, '').strip()

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

            # Generate a chat
            reactions_add('loading')

            answer = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': f'あなたは日本人の優秀なアシスタントです。名前は「{caches.username}」です。次の質問に日本語で簡潔に答えてください。',
                    },
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ],
                stream=False,
                options={
                    'temperature': 0,
                },
            ).get('message', {}).get('content', 'わかりません'). strip()

            # **hoge** -> hoge
            answer = answer.replace('**', '')
            post(answer)

            reactions_remove('loading')

            return
