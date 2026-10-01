"""產生 App 用的預錄音檔（微軟神經語音，透過 edge-tts）。

用法（第一次要先裝 edge-tts）：
    python3 -m venv ~/.venvs/tts && ~/.venvs/tts/bin/pip install edge-tts
    ~/.venvs/tts/bin/python tools/gen_audio.py

只會產生「新增或文字有改過」的音檔；audio/index.json 記錄每個檔案當初念的文字和聲音。
"""
import asyncio, json, os, re
import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')
VOICES = {'m': 'de-DE-ConradNeural', 'f': 'de-DE-SeraphinaMultilingualNeural'}
RATE = '-10%'          # Seraphina 原速偏快，整體放慢一點
WORD_VOICE = 'f'       # 單字、例句用 Seraphina


def tts_text(text):
    # 拼字句「L – I – N」改成逗號，一個字母一個字母念
    return re.sub(r'\s[–-]\s', ', ', text)


def jobs():
    vocab = json.load(open(os.path.join(ROOT, 'vocab.json')))
    dialogues = json.load(open(os.path.join(ROOT, 'dialogues.json')))
    for v in vocab:
        yield f"{v['id']}.mp3", v['de'], WORD_VOICE
        yield f"{v['id']}_ex.mp3", v['example_de'], WORD_VOICE
    for d in dialogues:
        for i, line in enumerate(d['lines']):
            yield f"{d['id']}_{i:02d}.mp3", line['de'], d['voices'][line['speaker']]


async def main():
    os.makedirs(AUDIO, exist_ok=True)
    index_path = os.path.join(AUDIO, 'index.json')
    index = json.load(open(index_path)) if os.path.exists(index_path) else {}
    todo = [(f, t, v) for f, t, v in jobs()
            if index.get(f) != {'text': t, 'voice': VOICES[v]} or not os.path.exists(os.path.join(AUDIO, f))]
    print(f'需要產生 {len(todo)} 個音檔')
    sem = asyncio.Semaphore(4)

    async def one(f, text, v):
        async with sem:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(tts_text(text), VOICES[v], rate=RATE).save(os.path.join(AUDIO, f))
                    index[f] = {'text': text, 'voice': VOICES[v]}
                    return
                except Exception as e:
                    if attempt == 2:
                        print(f'失敗：{f}（{e}）')
                    await asyncio.sleep(2)

    await asyncio.gather(*(one(*j) for j in todo))
    # 只保留目前資料還用得到的紀錄
    wanted = {f for f, _, _ in jobs()}
    index = {k: index[k] for k in sorted(index) if k in wanted}
    json.dump(index, open(index_path, 'w'), ensure_ascii=False, indent=1)
    stale = sorted(set(os.listdir(AUDIO)) - wanted - {'index.json'})
    if stale:
        print('這些音檔已沒有對應資料，可手動移到垃圾桶：', ' '.join(stale))
    print(f'完成，共 {len(index)} 個音檔')


asyncio.run(main())
